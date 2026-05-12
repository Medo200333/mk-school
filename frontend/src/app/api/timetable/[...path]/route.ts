
export const dynamic = "force-dynamic";
const BACKEND = process.env.API_INTERNAL_BASE_URL || "http://backend:8000";

async function forward(req: Request, path: string[]) {
  const url = `${BACKEND}/api/v1/school-timetable/${path.join("/")}`;
  const init: RequestInit = { method: req.method, headers: {"Content-Type": req.headers.get("content-type") || "application/json"} };
  if (req.method !== "GET" && req.method !== "HEAD") init.body = await req.text();
  const res = await fetch(url, init);
  return new Response(await res.text(), { status: res.status, headers: {"Content-Type": res.headers.get("content-type") || "application/json"} });
}

export async function GET(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  const params = await ctx.params;
  return forward(req, params.path);
}
export async function POST(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  const params = await ctx.params;
  return forward(req, params.path);
}
export async function DELETE(req: Request, ctx: { params: Promise<{ path: string[] }> }) {
  const params = await ctx.params;
  return forward(req, params.path);
}
