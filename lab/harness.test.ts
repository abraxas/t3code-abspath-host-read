import * as NodeFS from "node:fs";

import * as NodeCrypto from "@effect/platform-node/NodeCrypto";
import * as NodeServices from "@effect/platform-node/NodeServices";
import {
  AuthFilesystemReadScope,
  AuthOrchestrationReadScope,
  AuthStandardClientScopes,
  mcpClientScopes,
  WS_METHODS,
} from "@t3tools/contracts";
import * as HostProcess from "@t3tools/shared/HostProcess";
import { describe, expect, it } from "@effect/vitest";
import * as Effect from "effect/Effect";
import * as Layer from "effect/Layer";
import * as Path from "effect/Path";

import { requiredScopeForRpcMethod, rpcAuthorizationError } from "../auth/RpcAuthorization.ts";
import * as ServerConfig from "../config.ts";
import * as VcsDriverRegistry from "../vcs/VcsDriverRegistry.ts";
import * as VcsProcess from "../vcs/VcsProcess.ts";
import * as KnownWorkspaces from "./KnownWorkspaces.ts";
import * as WorkspaceEntries from "./WorkspaceEntries.ts";
import * as WorkspaceFileSystem from "./WorkspaceFileSystem.ts";
import * as WorkspacePaths from "./WorkspacePaths.ts";

const UNKNOWN_WORKSPACE_PREFIX = "t3code-unknown-workspace-";
const layerKnownWorkspacesTest = Layer.mock(KnownWorkspaces.KnownWorkspaces)({
  assertContains: (cwd) =>
    cwd.includes(UNKNOWN_WORKSPACE_PREFIX)
      ? Effect.fail(new KnownWorkspaces.UnknownWorkspaceError({ cwd }))
      : Effect.void,
});

const layerProject = WorkspaceFileSystem.layer.pipe(
  Layer.provide(layerKnownWorkspacesTest),
  Layer.provide(WorkspacePaths.layer),
  Layer.provide(WorkspaceEntries.layer.pipe(Layer.provide(WorkspacePaths.layer))),
);

const layerTest = Layer.empty.pipe(
  Layer.provideMerge(layerProject),
  Layer.provideMerge(WorkspaceEntries.layer.pipe(Layer.provide(WorkspacePaths.layer))),
  Layer.provideMerge(WorkspacePaths.layer),
  Layer.provideMerge(VcsDriverRegistry.layer.pipe(Layer.provide(VcsProcess.layer))),
  Layer.provideMerge(
    ServerConfig.ServerConfig.layerTest(process.cwd(), {
      prefix: "t3-f01-abspath-test-",
    }),
  ),
  Layer.provideMerge(Layer.mergeAll(NodeServices.layer, NodeCrypto.layer)),
);

type LabResult = {
  absRead: 0 | 1;
  homeRead: 0 | 1;
  relEscape: 0 | 1;
  writeAbs: "refused" | "unexpected";
  mcpReadonlyFilesystem: "denied" | "granted" | "skipped";
  absContents: string;
  homeContents: string;
  relTag: string;
  writeTag: string;
  secretUnchanged: boolean;
  usedOperatorHome: boolean;
};

const requiredEnv = (name: string): string => {
  const value = process.env[name];
  if (!value) throw new Error(`missing ${name}`);
  return value;
};

const containsWitness = (text: string, witness: string): boolean => text.includes(witness);

const writeResult = (result: LabResult): void => {
  const resultPath = requiredEnv("LAB_RESULT_PATH");
  NodeFS.writeFileSync(resultPath, `${JSON.stringify(result, null, 2)}\n`);
};

it.layer(layerTest, { excludeTestServices: true })("T3-F01-ABSPATH", (it) => {
  describe("WorkspaceFileSystem host reads", () => {
    it.effect("returns planted witness for abs and ~/ and refuses write-abs and rel-escape", () =>
      Effect.gen(function* () {
        const labHome = requiredEnv("LAB_HOME");
        const workspace = requiredEnv("LAB_WORKSPACE");
        const secretPath = requiredEnv("LAB_SECRET_PATH");
        const witness = requiredEnv("LAB_WITNESS");
        const secretBefore = NodeFS.readFileSync(secretPath, "utf8");
        const workspaceFileSystem = yield* WorkspaceFileSystem.WorkspaceFileSystem;
        const path = yield* Path.Path;
        const result: LabResult = {
          absRead: 0,
          homeRead: 0,
          relEscape: 0,
          writeAbs: "unexpected",
          mcpReadonlyFilesystem: "skipped",
          absContents: "",
          homeContents: "",
          relTag: "",
          writeTag: "",
          secretUnchanged: false,
          usedOperatorHome: false,
        };

        const abs = yield* Effect.result(
          workspaceFileSystem.readFile({ cwd: workspace, relativePath: secretPath }),
        );
        if (abs._tag === "Success") {
          result.absContents = abs.success.contents;
          result.absRead = containsWitness(abs.success.contents, witness) ? 1 : 0;
        } else {
          result.absContents = `${abs.failure._tag}:${abs.failure.message}`;
        }

        const home = yield* Effect.result(
          workspaceFileSystem
            .readFile({ cwd: workspace, relativePath: "~/.lab-secret" })
            .pipe(Effect.provideService(HostProcess.HomeDirectory, labHome)),
        );
        if (home._tag === "Success") {
          result.homeContents = home.success.contents;
          result.homeRead = containsWitness(home.success.contents, witness) ? 1 : 0;
        } else {
          result.homeContents = `${home.failure._tag}:${home.failure.message}`;
        }

        const relativeEscape = path.relative(workspace, secretPath);
        const rel = yield* Effect.result(
          workspaceFileSystem.readFile({ cwd: workspace, relativePath: relativeEscape }),
        );
        if (rel._tag === "Success") {
          result.relTag = "contents";
          result.relEscape = containsWitness(rel.success.contents, witness) ? 1 : 0;
        } else {
          result.relTag = rel.failure._tag;
          result.relEscape = containsWitness(rel.failure.message, witness) ? 1 : 0;
        }

        const write = yield* Effect.result(
          workspaceFileSystem.writeFile({
            cwd: workspace,
            relativePath: secretPath,
            contents: "MUTATED\n",
          }),
        );
        if (write._tag === "Failure") {
          result.writeTag = write.failure._tag;
          result.writeAbs =
            write.failure._tag === "WorkspacePathOutsideRootError" ||
            write.failure._tag === "WorkspaceFilePathEscapeError"
              ? "refused"
              : "unexpected";
        } else {
          result.writeTag = "wrote";
          result.writeAbs = "unexpected";
        }

        const secretAfter = NodeFS.readFileSync(secretPath, "utf8");
        result.secretUnchanged = secretAfter === secretBefore;
        result.usedOperatorHome = !secretPath.startsWith(labHome);

        const mcpScopes = mcpClientScopes("read-only");
        const required = requiredScopeForRpcMethod(WS_METHODS.projectsReadFile);
        const missing = [required].find((scope) => !mcpScopes.includes(scope));
        result.mcpReadonlyFilesystem =
          missing === AuthFilesystemReadScope &&
          mcpScopes.length === 1 &&
          mcpScopes[0] === AuthOrchestrationReadScope
            ? "denied"
            : mcpScopes.includes(AuthFilesystemReadScope)
              ? "granted"
              : "skipped";

        expect(AuthStandardClientScopes).toContain(AuthFilesystemReadScope);
        expect(required).toBe(AuthFilesystemReadScope);
        writeResult(result);
        expect(result.absRead).toBe(1);
        expect(result.homeRead).toBe(1);
        expect(result.relEscape).toBe(0);
        expect(result.writeAbs).toBe("refused");
        expect(result.secretUnchanged).toBe(true);
        expect(result.usedOperatorHome).toBe(false);
        expect(result.mcpReadonlyFilesystem).toBe("denied");
        expect(rpcAuthorizationError(required).message).toContain("filesystem:read");
      }),
    );
  });
});
