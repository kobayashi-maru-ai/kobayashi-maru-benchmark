import { getPublicRun, getPublicRunIds } from "@/lib/results";

export const dynamic = "force-static";
export const dynamicParams = false;

type Context = { params: Promise<{ runId: string }> };

export async function generateStaticParams() {
  return (await getPublicRunIds()).map((runId) => ({ runId }));
}

export async function GET(_request: Request, context: Context) {
  const { runId } = await context.params;
  const run = await getPublicRun(runId);
  if (!run) {
    return Response.json({ error: "Run not found" }, { status: 404 });
  }
  return Response.json(run);
}
