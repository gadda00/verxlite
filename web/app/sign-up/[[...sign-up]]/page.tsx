"use client";

import { SignUp } from "@clerk/nextjs";
import Link from "next/link";
import { Button } from "@/components/ui/button";

// Verxlite brand components
const VerxliteLogo = () => (
  <div className="flex items-center space-x-2">
    <div className="w-8 h-8 bg-verxlite-neon rounded-lg flex items-center justify-center">
      <span className="text-verxlite-dark font-bold text-lg">V</span>
    </div>
    <span className="text-xl font-bold text-verxlite-neon">Verxlite</span>
  </div>
);

export default function SignUpPage() {
  return (
    <div className="min-h-screen bg-verxlite-dark flex flex-col">
      <header className="py-4 px-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <VerxliteLogo />
          <Button
            variant="ghost"
            className="text-white hover:text-verxlite-neon hover:bg-white/10"
            asChild
          >
            <Link href="/">Home</Link>
          </Button>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-lg shadow-xl p-8">
            <div className="text-center mb-8">
              <VerxliteLogo />
              <h1 className="text-2xl font-bold text-gray-900 mt-4">
                Create an Account
              </h1>
              <p className="text-gray-600 mt-2">
                Join Verxlite to automate your workflows
              </p>
            </div>

            <SignUp
              path="/sign-up"
              routing="path"
              signInUrl="/login"
              appearance={
                elements: {
                  rootBox: "w-full",
                  card: "shadow-none border-none",
                  headerTitle: "text-xl font-bold text-gray-900",
                  headerSubtitle: "text-gray-600",
                  socialButtonsBlock: "gap-4",
                  socialButtons: "w-full",
                  dividerLine: "bg-gray-200",
                  dividerText: "text-gray-500",
                  formField: "mb-4",
                  formLabel: "text-gray-700",
                  formInput: "w-full border-gray-300 rounded-md px-3 py-2",
                  formButtonPrimary: "w-full bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90",
                  footer: "mt-6",
                  footerActionLink: "text-verxlite-neon hover:underline",
                },
              }}
            />
          </div>
        </div>
      </main>

      <footer className="py-8 px-4 bg-white/10">
        <div className="max-w-6xl mx-auto text-center">
          <p className="text-gray-400">
            Verxlite - The weight of manual work, lifted.
          </p>
        </div>
      </footer>
    </div>
  );
}
