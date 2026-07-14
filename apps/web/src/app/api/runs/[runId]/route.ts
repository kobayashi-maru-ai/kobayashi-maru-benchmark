import { getPublicRun } from "@/lib/results";

export const dynamic = "force-static";

type Context = { params: Promise<{ runId: string }> };

export async function GET(_request: Request, context: Context) {
  const { runId } = await context.params;
  const run = await getPublicRun(runId);
  if (!run) {
    return Response.json({ error: "Run not found" }, { status: 404 });
  }
  return Response.json(run);
}
