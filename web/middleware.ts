import { withClerkMiddleware } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

// Clerk v4 middleware — enables auth context on every request.
// Route protection is enforced client-side in each page (see `useUser`).
export default withClerkMiddleware(() => {
  return NextResponse.next();
});

export const config = {
  matcher: [
    // Skip Next.js internals and static files
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|pdf)).*)",
    // Always run for API routes
    "/(api|trpc)(.*)",
  ],
};
