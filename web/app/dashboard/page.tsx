"use client";

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";

// Verxlite brand components
const VerxliteLogo = () => (
  <div className="flex items-center space-x-2">
    <div className="w-8 h-8 bg-verxlite-neon rounded-lg flex items-center justify-center">
      <span className="text-verxlite-dark font-bold text-lg">V</span>
    </div>
    <span className="text-xl font-bold text-verxlite-neon">Verxlite</span>
  </div>
);

// Mock data for workflow runs
const mockWorkflowRuns = [
  {
    id: "run_1",
    workflow_name: "Post-Meeting Followup",
    status: "completed",
    trigger_type: "calendar_event_ended",
    created_at: "2024-01-15T10:30:00Z",
    total_tokens: 1500,
    total_duration_ms: 2500,
  },
  {
    id: "run_2",
    workflow_name: "Post-Meeting Followup",
    status: "completed",
    trigger_type: "calendar_event_ended",
    created_at: "2024-01-14T14:15:00Z",
    total_tokens: 1200,
    total_duration_ms: 2000,
  },
  {
    id: "run_3",
    workflow_name: "Post-Meeting Followup",
    status: "failed",
    trigger_type: "manual",
    created_at: "2024-01-13T09:45:00Z",
    total_tokens: 800,
    total_duration_ms: 1500,
  },
];

const mockConnections = [
  { id: "conn_1", provider: "google", is_active: true, created_at: "2024-01-01" },
  { id: "conn_2", provider: "hubspot", is_active: true, created_at: "2024-01-02" },
];

const mockStats = {
  total_runs: 42,
  successful_runs: 38,
  failed_runs: 4,
  total_tokens: 50000,
  avg_duration_ms: 1800,
};

export default function DashboardPage() {
  const { isSignedIn, user } = useUser();
  const router = useRouter();
  const [workflowRuns, setWorkflowRuns] = useState(mockWorkflowRuns);
  const [connections, setConnections] = useState(mockConnections);
  const [stats, setStats] = useState(mockStats);

  useEffect(() => {
    if (!isSignedIn) {
      router.push("/login");
    }
  }, [isSignedIn, router]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge variant="default">Completed</Badge>;
      case "running":
        return <Badge variant="secondary">Running</Badge>;
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatDuration = (ms: number) => {
    return `${(ms / 1000).toFixed(1)}s`;
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
              variant="ghost"
              className="text-white hover:text-verxlite-neon hover:bg-white/10"
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
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">
            Welcome back, {user?.fullName || user?.emailAddresses[0]?.emailAddress}!
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
              <div className="w-8 h-8 bg-verxlite-neon rounded-lg flex items-center justify-center">
                <span className="text-verxlite-dark text-sm">📊</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_runs}</div>
              <p className="text-xs text-muted-foreground">
                +12% from last week
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm">✓</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {((stats.successful_runs / stats.total_runs) * 100).toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                {stats.successful_runs} successful runs
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm">🔑</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_tokens.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                tokens used
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
              <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm">⚡</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatDuration(stats.avg_duration_ms)}</div>
              <p className="text-xs text-muted-foreground">
                per run
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Workflow Runs */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Recent Workflow Runs</h2>
            <Button className="bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90">
              <Link href="/workflows">View All</Link>
            </Button>
          </div>

          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Workflow</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Trigger</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Tokens</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workflowRuns.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell className="font-medium">{run.workflow_name}</TableCell>
                    <TableCell>{getStatusBadge(run.status)}</TableCell>
                    <TableCell>{run.trigger_type}</TableCell>
                    <TableCell>{formatDate(run.created_at)}</TableCell>
                    <TableCell>{formatDuration(run.total_duration_ms)}</TableCell>
                    <TableCell>{run.total_tokens.toLocaleString()}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        asChild
                      >
                        <Link href={`/workflows/runs/${run.id}`}>View</Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </div>

        {/* Connections */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Connections</h2>
            <Button className="bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90">
              <Link href="/connections">Manage</Link>
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {connections.map((conn) => (
              <Card key={conn.id}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="capitalize">{conn.provider}</span>
                    {conn.is_active ? (
                      <Badge variant="default">Active</Badge>
                    ) : (
                      <Badge variant="destructive">Inactive</Badge>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    Connected on {formatDate(conn.created_at)}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
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
