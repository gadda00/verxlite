"use client";

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

// Verxlite brand components
const VerxliteLogo = () => (
  <div className="flex items-center space-x-2">
    <div className="w-8 h-8 bg-verxlite-neon rounded-lg flex items-center justify-center">
      <span className="text-verxlite-dark font-bold text-lg">V</span>
    </div>
    <span className="text-xl font-bold text-verxlite-neon">Verxlite</span>
  </div>
);

// Mock user data
const mockUser = {
  id: "user_abc123",
  email: "john@acme.com",
  firstName: "John",
  lastName: "Doe",
  role: "admin",
  timezone: "America/New_York",
  avatarUrl: "https://example.com/avatar.jpg",
};

const mockTenant = {
  id: "tenant_abc123",
  name: "Acme Corp",
  subscriptionPlan: "pro",
  subscriptionStatus: "active",
  trialEndsAt: null,
};

const mockConnections = [
  { id: "conn_1", provider: "google", is_active: true, is_expired: false, scope: "email,profile,calendar.readonly" },
  { id: "conn_2", provider: "hubspot", is_active: true, is_expired: false, scope: "contacts,content,automation" },
];

export default function SettingsPage() {
  const { isLoaded, isSignedIn, user } = useUser();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("profile");
  const [userData, setUserData] = useState(mockUser);
  const [tenantData, setTenantData] = useState(mockTenant);
  const [connections, setConnections] = useState(mockConnections);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.push("/login");
    }
  }, [isLoaded, isSignedIn, router]);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    setError(null);
    setSuccess(null);
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      // In production, call API to update profile
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSuccess("Profile updated successfully!");
    } catch (err) {
      setError("Failed to update profile. Please try again.");
    } finally {
      setIsLoading(false);
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

  const handleRefreshToken = async (connectionId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // In production, call API to refresh token
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSuccess("Token refreshed successfully!");
    } catch (err) {
      setError("Failed to refresh token. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (isActive: boolean, isExpired: boolean) => {
    if (!isActive) {
      return <Badge variant="destructive">Inactive</Badge>;
    }
    if (isExpired) {
      return <Badge variant="destructive">Expired</Badge>;
    }
    return <Badge variant="default">Active</Badge>;
  };

  if (!isLoaded || !isSignedIn) {
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
              variant="ghost"
              className="text-white hover:text-verxlite-neon hover:bg-white/10"
              asChild
            >
              <Link href="/connections">Connections</Link>
            </Button>
            <Button
              variant="secondary"
              className="bg-verxlite-neon/20 text-verxlite-neon border-verxlite-neon"
              asChild
            >
              <Link href="/settings">Settings</Link>
            </Button>
          </nav>
        </div>
      </header>

      <main className="max-w-4xl mx-auto py-8 px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600">
            Manage your account, connections, and preferences
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => handleTabChange("profile")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === "profile"
                  ? "border-verxlite-neon text-verxlite-neon"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Profile
            </button>
            <button
              onClick={() => handleTabChange("connections")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === "connections"
                  ? "border-verxlite-neon text-verxlite-neon"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Connections
            </button>
            <button
              onClick={() => handleTabChange("tenant")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === "tenant"
                  ? "border-verxlite-neon text-verxlite-neon"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Tenant
            </button>
            <button
              onClick={() => handleTabChange("notifications")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === "notifications"
                  ? "border-verxlite-neon text-verxlite-neon"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Notifications
            </button>
            <button
              onClick={() => handleTabChange("billing")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === "billing"
                  ? "border-verxlite-neon text-verxlite-neon"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Billing
            </button>
          </nav>
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

        {/* Tab Content */}
        <div className="space-y-8">
          {/* Profile Tab */}
          {activeTab === "profile" && (
            <Card>
              <CardHeader>
                <CardTitle>Profile Settings</CardTitle>
                <CardDescription>
                  Update your personal information
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleUpdateProfile} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <Label htmlFor="firstName">First Name</Label>
                      <Input
                        id="firstName"
                        value={userData.firstName || ""}
                        onChange={(e) => setUserData({...userData, firstName: e.target.value})}
                        placeholder="John"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lastName">Last Name</Label>
                      <Input
                        id="lastName"
                        value={userData.lastName || ""}
                        onChange={(e) => setUserData({...userData, lastName: e.target.value})}
                        placeholder="Doe"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={userData.email || ""}
                        readOnly
                        className="bg-gray-100 cursor-not-allowed"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="timezone">Timezone</Label>
                      <Input
                        id="timezone"
                        value={userData.timezone || ""}
                        onChange={(e) => setUserData({...userData, timezone: e.target.value})}
                        placeholder="America/New_York"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <Switch id="email-notifications" defaultChecked />
                      <Label htmlFor="email-notifications">Email Notifications</Label>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Receive email notifications for workflow events
                    </p>
                  </div>
                  
                  <Button
                    type="submit"
                    className="bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90"
                    disabled={isLoading}
                  >
                    {isLoading ? "Saving..." : "Save Changes"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Connections Tab */}
          {activeTab === "connections" && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Connected Services</CardTitle>
                  <CardDescription>
                    Manage your connections to external services
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {connections.length === 0 ? (
                      <div className="text-center py-8">
                        <p className="text-gray-500 mb-4">No connections yet</p>
                        <Button
                          className="bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90"
                          asChild
                        >
                          <Link href="/connections">Connect a Service</Link>
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {connections.map((conn) => (
                          <div
                            key={conn.id}
                            className="flex items-center justify-between p-4 border rounded-lg"
                          >
                            <div className="flex items-center space-x-4">
                              <div className="w-10 h-10 bg-verxlite-neon/20 rounded-lg flex items-center justify-center">
                                <span className="text-verxlite-neon font-bold text-sm">
                                  {conn.provider === "google" ? "G" : "H"}
                                </span>
                              </div>
                              <div>
                                <h3 className="font-semibold text-gray-900 capitalize">
                                  {conn.provider}
                                </h3>
                                <p className="text-sm text-gray-500">
                                  {conn.scope}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center space-x-4">
                              {getStatusBadge(conn.is_active, conn.is_expired)}
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRefreshToken(conn.id)}
                                disabled={isLoading}
                              >
                                Refresh
                              </Button>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => handleDisconnect(conn.id)}
                                disabled={isLoading}
                              >
                                Disconnect
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Connect New Service</CardTitle>
                  <CardDescription>
                    Add a new connection to an external service
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Button
                      className="h-16 justify-start space-x-3 bg-white border border-gray-200 hover:bg-gray-50"
                      asChild
                    >
                      <Link href="/connections/google/authorize">
                        <div className="w-8 h-8 bg-red-500 rounded flex items-center justify-center">
                          <span className="text-white text-sm">G</span>
                        </div>
                        <span className="font-medium">Google Workspace</span>
                      </Link>
                    </Button>
                    <Button
                      className="h-16 justify-start space-x-3 bg-white border border-gray-200 hover:bg-gray-50"
                      asChild
                    >
                      <Link href="/connections/hubspot/authorize">
                        <div className="w-8 h-8 bg-orange-500 rounded flex items-center justify-center">
                          <span className="text-white text-sm">H</span>
                        </div>
                        <span className="font-medium">HubSpot</span>
                      </Link>
                    </Button>
                    <Button
                      className="h-16 justify-start space-x-3 bg-white border border-gray-200 hover:bg-gray-50"
                      disabled
                    >
                      <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">
                        <span className="text-white text-sm">S</span>
                      </div>
                      <span className="font-medium">Salesforce</span>
                      <Badge variant="secondary" className="ml-auto">Coming Soon</Badge>
                    </Button>
                    <Button
                      className="h-16 justify-start space-x-3 bg-white border border-gray-200 hover:bg-gray-50"
                      disabled
                    >
                      <div className="w-8 h-8 bg-blue-800 rounded flex items-center justify-center">
                        <span className="text-white text-sm">O</span>
                      </div>
                      <span className="font-medium">Outlook</span>
                      <Badge variant="secondary" className="ml-auto">Coming Soon</Badge>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Tenant Tab */}
          {activeTab === "tenant" && (
            <Card>
              <CardHeader>
                <CardTitle>Tenant Settings</CardTitle>
                <CardDescription>
                  Manage your organization settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label>Tenant Name</Label>
                  <Input
                    value={tenantData.name || ""}
                    onChange={(e) => setTenantData({...tenantData, name: e.target.value})}
                    placeholder="Acme Corp"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Subscription Plan</Label>
                  <div className="flex items-center space-x-2">
                    <Badge variant={tenantData.subscriptionPlan === "pro" ? "default" : "secondary"}>
                      {tenantData.subscriptionPlan}
                    </Badge>
                    {tenantData.subscriptionStatus === "trial" && (
                      <Badge variant="outline">Trial</Badge>
                    )}
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Switch id="auto-assign" defaultChecked />
                    <Label htmlFor="auto-assign">Auto-assign new leads</Label>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Automatically assign new leads to available reps
                  </p>
                </div>
                
                <Button
                  className="bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90"
                  disabled={isLoading}
                >
                  {isLoading ? "Saving..." : "Save Changes"}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Notifications Tab */}
          {activeTab === "notifications" && (
            <Card>
              <CardHeader>
                <CardTitle>Notification Settings</CardTitle>
                <CardDescription>
                  Configure how you receive notifications
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Workflow Completion</h3>
                      <p className="text-sm text-muted-foreground">
                        Notify when a workflow completes
                      </p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Workflow Failure</h3>
                      <p className="text-sm text-muted-foreground">
                        Notify when a workflow fails
                      </p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">New Connection</h3>
                      <p className="text-sm text-muted-foreground">
                        Notify when a new service is connected
                      </p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">Token Expiration</h3>
                      <p className="text-sm text-muted-foreground">
                        Notify when a token is about to expire
                      </p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                </div>
                
                <Button
                  className="bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90"
                  disabled={isLoading}
                >
                  {isLoading ? "Saving..." : "Save Changes"}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Billing Tab */}
          {activeTab === "billing" && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Subscription</CardTitle>
                  <CardDescription>
                    Manage your subscription and billing
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-bold">Pro Plan</h3>
                      <p className="text-gray-500">
                        ${mockTenant.subscriptionPlan === "pro" ? "99" : "49"}/month
                      </p>
                    </div>
                    <Badge variant={mockTenant.subscriptionStatus === "active" ? "default" : "secondary"}>
                      {mockTenant.subscriptionStatus}
                    </Badge>
                  </div>
                  
                  <div className="border-t pt-6">
                    <h4 className="font-medium mb-4">Plan Features</h4>
                    <ul className="space-y-2">
                      <li className="flex items-center space-x-2">
                        <span className="text-green-500">✓</span>
                        <span>Unlimited workflows</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <span className="text-green-500">✓</span>
                        <span>Multiple connections</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <span className="text-green-500">✓</span>
                        <span>Priority support</span>
                      </li>
                      <li className="flex items-center space-x-2">
                        <span className="text-green-500">✓</span>
                        <span>Advanced analytics</span>
                      </li>
                    </ul>
                  </div>
                  
                  <div className="flex space-x-4">
                    <Button
                      variant="outline"
                      className="w-full"
                    >
                      Manage Subscription
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full"
                    >
                      View Invoices
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Usage</CardTitle>
                  <CardDescription>
                    Your current usage for this billing period
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span>Workflow Runs</span>
                      <span className="font-medium">1,247 / 5,000</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-verxlite-neon h-2 rounded-full"
                        style={{ width: "25%" }}
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span>Tokens Used</span>
                      <span className="font-medium">150,000 / 1,000,000</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-verxlite-neon h-2 rounded-full"
                        style={{ width: "15%" }}
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span>Connections</span>
                      <span className="font-medium">2 / 10</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-verxlite-neon h-2 rounded-full"
                        style={{ width: "20%" }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </main>

      <footer className="py-8 px-4 bg-white border-t mt-12">
        <div className="max-w-6xl mx-auto text-center">
          <p className="text-gray-600">
            Verxlite - The weight of manual work, lifted.
          </p>
        </div>
      </footer>
    </div>
  );
}
