"use client";

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
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

const HeroSection = () => (
  <section className="relative bg-verxlite-dark text-white py-20 px-4">
    <div className="absolute inset-0 bg-gradient-to-br from-black/20 to-black/40" />
    <div className="relative max-w-6xl mx-auto text-center">
      <h1 className="text-5xl md:text-7xl font-bold mb-6">
        Stop Logging. Start Closing.
      </h1>
      <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
        Verxlite is the universal AI agent that turns your meetings into CRM updates, 
        follow-ups, and tasks. Instantly. Zero data entry.
      </p>
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <Button
          size="lg"
          className="bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90 font-semibold px-8 py-3"
        >
          Get Started
        </Button>
        <Button
          size="lg"
          variant="outline"
          className="border-verxlite-neon text-verxlite-neon hover:bg-verxlite-neon/10 font-semibold px-8 py-3"
        >
          Learn More
        </Button>
      </div>
    </div>
  </section>
);

const HowItWorks = () => (
  <section className="py-20 px-4 bg-white">
    <div className="max-w-6xl mx-auto">
      <h2 className="text-4xl font-bold text-center mb-16 text-gray-900">
        How It Works
      </h2>
      
      <div className="grid md:grid-cols-3 gap-12">
        <div className="text-center">
          <div className="w-16 h-16 bg-verxlite-neon rounded-full flex items-center justify-center mx-auto mb-6">
            <span className="text-2xl">1</span>
          </div>
          <h3 className="text-2xl font-bold mb-4 text-gray-900">
            You finish a meeting
          </h3>
          <p className="text-gray-600">
            Verxlite detects it automatically from your calendar.
          </p>
        </div>
        
        <div className="text-center">
          <div className="w-16 h-16 bg-verxlite-neon rounded-full flex items-center justify-center mx-auto mb-6">
            <span className="text-2xl">2</span>
          </div>
          <h3 className="text-2xl font-bold mb-4 text-gray-900">
            Verxlite listens & learns
          </h3>
          <p className="text-gray-600">
            AI extracts action items, deal details, and next steps.
          </p>
        </div>
        
        <div className="text-center">
          <div className="w-16 h-16 bg-verxlite-neon rounded-full flex items-center justify-center mx-auto mb-6">
            <span className="text-2xl">3</span>
          </div>
          <h3 className="text-2xl font-bold mb-4 text-gray-900">
            Your CRM is updated
          </h3>
          <p className="text-gray-600">
            Notes logged, tasks created, follow-up drafted. You just click &apos;Send&apos;.
          </p>
        </div>
      </div>
    </div>
  </section>
);

const Features = () => (
  <section className="py-20 px-4 bg-gray-50">
    <div className="max-w-6xl mx-auto">
      <h2 className="text-4xl font-bold text-center mb-16 text-gray-900">
        Features
      </h2>
      
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-xl font-bold mb-3 text-gray-900">
            Auto-Logging
          </h3>
          <p className="text-gray-600">
            Automatically log meeting notes to your CRM.
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-xl font-bold mb-3 text-gray-900">
            Follow-Up Emails
          </h3>
          <p className="text-gray-600">
            Draft personalized follow-up emails instantly.
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-xl font-bold mb-3 text-gray-900">
            Task Creation
          </h3>
          <p className="text-gray-600">
            Create tasks in your CRM with due dates.
          </p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-xl font-bold mb-3 text-gray-900">
            Universal
          </h3>
          <p className="text-gray-600">
            Works with any CRM and email provider.
          </p>
        </div>
      </div>
    </div>
  </section>
);

const CTA = () => (
  <section className="py-20 px-4 bg-verxlite-dark text-white">
    <div className="max-w-4xl mx-auto text-center">
      <h2 className="text-4xl font-bold mb-6">
        Ready to Automate Your Workflows?
      </h2>
      <p className="text-xl text-gray-300 mb-8">
        Join hundreds of teams saving hours every week with Verxlite.
      </p>
      <Button
        size="lg"
        className="bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90 font-semibold px-8 py-3"
      >
        Get Started Free
      </Button>
    </div>
  </section>
);

const Footer = () => (
  <footer className="py-12 px-4 bg-white border-t">
    <div className="max-w-6xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-center">
        <VerxliteLogo />
        <p className="text-gray-600 mt-4 md:mt-0">
          Verxlite - The weight of manual work, lifted.
        </p>
      </div>
    </div>
  </footer>
);

export default function Home() {
  const { isSignedIn, user } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (isSignedIn) {
      router.push("/dashboard");
    }
  }, [isSignedIn, router]);

  return (
    <div className="min-h-screen">
      <header className="py-4 px-4 bg-verxlite-dark">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <VerxliteLogo />
          <nav className="flex items-center space-x-6">
            <Link href="#features" className="text-white hover:text-verxlite-neon">
              Features
            </Link>
            <Link href="#how-it-works" className="text-white hover:text-verxlite-neon">
              How It Works
            </Link>
            <Button
              variant="ghost"
              className="text-white hover:text-verxlite-neon hover:bg-white/10"
              asChild
            >
              <Link href="/login">Login</Link>
            </Button>
          </nav>
        </div>
      </header>

      <main>
        <HeroSection />
        <HowItWorks />
        <Features />
        <CTA />
      </main>

      <Footer />
    </div>
  );
}
