"use client";

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";

// Verxlite brand components
const VerxliteLogo = () => (
  <div className="flex items-center space-x-2">
    <div className="w-8 h-8 bg-verxlite-neon rounded-lg flex items-center justify-center">
      <span className="text-verxlite-dark font-bold text-lg">V</span>
    </div>
    <span className="text-xl font-bold text-verxlite-neon">Verxlite</span>
  </div>
);

// Mock connections data
const mockConnections = [
  {
    id: "conn_1",
    provider: "google",
    provider_user_id: "google_user_123",
    is_active: true,
    is_expired: false,
    scope: "email,profile,calendar.readonly,gmail.readonly",
    last_sync_at: "2024-01-15T10:30:00Z",
    sync_status: "success",
    created_at: "2024-01-01T12:00:00Z",
  },
  {
    id: "conn_2",
    provider: "hubspot",
    provider_user_id: null,
    is_active: true,
    is_expired: false,
    scope: "contacts,content,automation,crm.objects.contacts.read,crm.objects.contacts.write",
    last_sync_at: "2024-01-15T10:35:00Z",
    sync_status: "success",
    created_at: "2024-01-02T14:00:00Z",
  },
];

const providerConfig = {
  google: {
    name: "Google Workspace",
    description: "Connect to Gmail, Calendar, and Drive",
    color: "bg-red-500",
    icon: "G",
    scopes: [
      "email",
      "profile",
      "calendar.readonly",
      "calendar.events.readonly",
      "gmail.readonly",
      "gmail.modify",
      "drive.readonly",
    ],
  },
  hubspot: {
    name: "HubSpot",
    description: "Connect to CRM, contacts, and deals",
    color: "bg-orange-500",
    icon: "H",
    scopes: [
      "contacts",
      "content",
      "automation",
      "crm.objects.owners.read",
      "crm.objects.contacts.read",
      "crm.objects.contacts.write",
      "crm.objects.deals.read",
      "crm.objects.deals.write",
      "crm.objects.tasks.read",
      "crm.objects.tasks.write",
    ],
  },
  salesforce: {
    name: "Salesforce",
    description: "Connect to Salesforce CRM",
    color: "bg-blue-600",
    icon: "S",
    scopes: [],
    comingSoon: true,
  },
  outlook: {
    name: "Outlook",
    description: "Connect to Outlook email and calendar",
    color: "bg-blue-800",
    icon: "O",
    scopes: [],
    comingSoon: true,
  },
};

export default function ConnectionsPage() {
  const { isSignedIn, user } = useUser();
  const router = useRouter();
  const [connections, setConnections] = useState(mockConnections);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [syncing, setSyncing] = useState<string | null>(null);

  useEffect(() => {
    if (!isSignedIn) {
      router.push("/login");
    } else {
      // In production, fetch connections from API
      setTimeout(() => {
        setIsLoading(false);
      }, 1000);
    }
  }, [isSignedIn, router]);

  const getStatusBadge = (isActive: boolean, isExpired: boolean, syncStatus?: string) => {
    if (!isActive) {
      return <Badge variant="destructive">Inactive</Badge>;
    }
    if (isExpired) {
      return <Badge variant="destructive">Expired</Badge>;
    }
    if (syncStatus === "failed") {
      return <Badge variant="destructive">Sync Failed</Badge>;
    }
    if (syncStatus === "pending") {
      return <Badge variant="secondary">Syncing...</Badge>;
    }
    return <Badge variant="default">Active</Badge>;
  };

  const handleSync = async (connectionId: string) => {
    setSyncing(connectionId);
    setError(null);
    
    try {
      // In production, call API to sync
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setConnections(connections.map(conn => {
        if (conn.id === connectionId) {
          return {
            ...conn,
            last_sync_at: new Date().toISOString(),
            sync_status: "success",
          };
        }
        return conn;
      }));
      
      setSuccess("Sync completed successfully!");
    } catch (err) {
      setError("Failed to sync connection. Please try again.");
      setConnections(connections.map(conn => {
        if (conn.id === connectionId) {
          return {
            ...conn,
            sync_status: "failed",
          };
        }
        return conn;
      }));
    } finally {
      setSyncing(null);
    }
  };

  const handleDisconnect = async (connectionId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // In production, call API to disconnect
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setConnections(connections.filter(conn => conn.id !== connectionId));
      setSuccess("Connection disconnected successfully!");
    } catch (err) {
      setError("Failed to disconnect. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = (provider: string) => {
    // In production, redirect to OAuth endpoint
    router.push(`/connections/${provider}/authorize`);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (!isSignedIn) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="py-4 px-4 bg-verxlite-dark">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <VerxliteLogo />
          <nav className="flex items-center space-x-6">
            <Button
              variant="ghost"
              className="text-white hover:text-verxlite-neon hover:bg-white/10"
              asChild
            >
              <Link href="/dashboard">Dashboard</Link>
            </Button>
            <Button
              variant="ghost"
              className="text-white hover:text-verxlite-neon hover:bg-white/10"
              asChild
            >
              <Link href="/workflows">Workflows</Link>
            </Button>
            <Button
              variant="secondary"
              className="bg-verxlite-neon/20 text-verxlite-neon border-verxlite-neon"
              asChild
            >
              <Link href="/connections">Connections</Link>
            </Button>
            <Button
              variant="ghost"
              className="text-white hover:text-verxlite-neon hover:bg-white/10"
              asChild
            >
              <Link href="/settings">Settings</Link>
            </Button>
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto py-8 px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Connections</h1>
          <p className="text-gray-600">
            Connect external services to enable workflows
          </p>
        </div>

        {/* Alerts */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {success && (
          <Alert variant="default" className="mb-6 bg-green-50 border-green-200 text-green-800">
            <AlertTitle>Success</AlertTitle>
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}

        {/* Connected Services */}
        <div className="mb-12">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Connected Services</h2>
          </div>

          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-6 w-48" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-4 w-full mb-2" />
                    <Skeleton className="h-4 w-3/4" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : connections.length === 0 ? (
            <Card className="text-center py-12">
              <CardHeader>
                <CardTitle>No Connections Yet</CardTitle>
                <CardDescription>
                  Connect your first service to start automating workflows
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  className="bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90"
                  asChild
                >
                  <Link href="#connect">Connect a Service</Link>
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {connections.map((conn) => {
                const config = providerConfig[conn.provider as keyof typeof providerConfig];
                
                return (
                  <Card key={conn.id}>
                    <CardHeader className="flex flex-row items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className={`w-10 h-10 ${config?.color} rounded-lg flex items-center justify-center`}>
                          <span className="text-white font-bold">{config?.icon}</span>
                        </div>
                        <div>
                          <CardTitle className="text-xl">{config?.name || conn.provider}</CardTitle>
                          <CardDescription>
                            {conn.provider_user_id ? `Connected as ${conn.provider_user_id}` : "Connected"}
                          </CardDescription>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getStatusBadge(conn.is_active, conn.is_expired, conn.sync_status)}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <h3 className="font-medium mb-2">Scopes</h3>
                          <div className="flex flex-wrap gap-2">
                            {conn.scope?.split(",").map((scope) => (
                              <Badge key={scope} variant="outline" className="text-xs">
                                {scope}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <div>
                          <h3 className="font-medium mb-2">Details</h3>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Connected:</span>
                              <span>{formatDate(conn.created_at)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Last Sync:</span>
                              <span>{formatDate(conn.last_sync_at)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Sync Status:</span>
                              <span className="capitalize">{conn.sync_status || "N/A"}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex space-x-4 mt-6 pt-4 border-t">
                        <Button
                          variant="outline"
                          onClick={() => handleSync(conn.id)}
                          disabled={syncing === conn.id || !conn.is_active}
                        >
                          {syncing === conn.id ? "Syncing..." : "Sync Now"}
                        </Button>
                        <Button
                          variant="outline"
                          asChild
                        >
                          <Link href={`/connections/${conn.id}/edit`}>Edit</Link>
                        </Button>
                        <Button
                          variant="destructive"
                          onClick={() => handleDisconnect(conn.id)}
                          disabled={isLoading}
                        >
                          Disconnect
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        {/* Connect New Service */}
        <div id="connect" className="mb-12">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Connect New Service</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Google */}
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader className="flex flex-row items-center space-x-4">
                <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-xl font-bold">G</span>
                </div>
                <div>
                  <CardTitle>Google Workspace</CardTitle>
                  <CardDescription>
                    Connect to Gmail, Calendar, and Drive
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Required for: Email automation, calendar triggers, document access
                </p>
                <Button
                  className="w-full bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90"
                  onClick={() => handleConnect("google")}
                >
                  Connect Google
                </Button>
              </CardContent>
            </Card>

            {/* HubSpot */}
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader className="flex flex-row items-center space-x-4">
                <div className="w-12 h-12 bg-orange-500 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-xl font-bold">H</span>
                </div>
                <div>
                  <CardTitle>HubSpot</CardTitle>
                  <CardDescription>
                    Connect to CRM, contacts, and deals
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Required for: CRM automation, contact management, deal tracking
                </p>
                <Button
                  className="w-full bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90"
                  onClick={() => handleConnect("hubspot")}
                >
                  Connect HubSpot
                </Button>
              </CardContent>
            </Card>

            {/* Salesforce (Coming Soon) */}
            <Card className="hover:shadow-lg transition-shadow opacity-75">
              <CardHeader className="flex flex-row items-center space-x-4">
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-xl font-bold">S</span>
                </div>
                <div>
                  <CardTitle>Salesforce</CardTitle>
                  <CardDescription>
                    Connect to Salesforce CRM
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Required for: Salesforce CRM automation
                </p>
                <Button
                  className="w-full"
                  variant="outline"
                  disabled
                >
                  Coming Soon
                </Button>
              </CardContent>
            </Card>

            {/* Outlook (Coming Soon) */}
            <Card className="hover:shadow-lg transition-shadow opacity-75">
              <CardHeader className="flex flex-row items-center space-x-4">
                <div className="w-12 h-12 bg-blue-800 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-xl font-bold">O</span>
                </div>
                <div>
                  <CardTitle>Outlook</CardTitle>
                  <CardDescription>
                    Connect to Outlook email and calendar
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Required for: Outlook email automation, calendar triggers
                </p>
                <Button
                  className="w-full"
                  variant="outline"
                  disabled
                >
                  Coming Soon
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* How It Works */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle>How Connections Work</CardTitle>
            <CardDescription>
              Understand how Verxlite uses your connections
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              <div className="flex items-start space-x-4">
                <div className="w-8 h-8 bg-verxlite-neon rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-verxlite-dark text-sm">1</span>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Connect Your Account</h3>
                  <p className="text-gray-600">
                    Click "Connect" for a service and authorize Verxlite to access your data.
                    We only request the minimum permissions needed for workflows.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-4">
                <div className="w-8 h-8 bg-verxlite-neon rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-verxlite-dark text-sm">2</span>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Secure Token Storage</h3>
                  <p className="text-gray-600">
                    Your OAuth tokens are encrypted and stored securely. We never store your password,
                    and tokens are automatically refreshed when they expire.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-4">
                <div className="w-8 h-8 bg-verxlite-neon rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-verxlite-dark text-sm">3</span>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Enable Workflows</h3>
                  <p className="text-gray-600">
                    Once connected, you can create workflows that use these services.
                    Verxlite will automatically use your connections to perform actions.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>

      <footer className="py-8 px-4 bg-white border-t">
        <div className="max-w-6xl mx-auto text-center">
          <p className="text-gray-600">
            Verxlite - The weight of manual work, lifted.
          </p>
        </div>
      </footer>
    </div>
  );
}
