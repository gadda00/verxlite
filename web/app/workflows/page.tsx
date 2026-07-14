"use client";

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Play, Pause, Edit, Trash2, Eye, BarChart3 } from "lucide-react";

// Verxlite brand components
const VerxliteLogo = () => (
  <div className="flex items-center space-x-2">
    <div className="w-8 h-8 bg-verxlite-neon rounded-lg flex items-center justify-center">
      <span className="text-verxlite-dark font-bold text-lg">V</span>
    </div>
    <span className="text-xl font-bold text-verxlite-neon">Verxlite</span>
  </div>
);

// Mock workflows data
const mockWorkflows = [
  {
    id: "workflow_1",
    name: "Post-Meeting Followup",
    description: "Auto-log to CRM + draft follow-up email + create tasks",
    workflow_type: "post_meeting_followup",
    is_active: true,
    status: "active",
    priority: 5,
    total_runs: 42,
    success_rate: 0.95,
    last_run_at: "2024-01-15T10:30:00Z",
    created_at: "2024-01-01T12:00:00Z",
  },
  {
    id: "workflow_2",
    name: "Lead Assignment",
    description: "Assign new leads to reps with automated follow-up",
    workflow_type: "lead_assignment",
    is_active: false,
    status: "draft",
    priority: 3,
    total_runs: 0,
    success_rate: 0,
    last_run_at: null,
    created_at: "2024-01-05T14:00:00Z",
  },
];

const workflowTemplates = [
  {
    id: "template_1",
    name: "Post-Meeting Followup",
    description: "Auto-log to CRM + draft follow-up email + create tasks",
    workflow_type: "post_meeting_followup",
    category: "Sales",
    popularity: "Most Popular",
  },
  {
    id: "template_2",
    name: "Lead Assignment",
    description: "Assign new leads to reps with automated follow-up sequence",
    workflow_type: "lead_assignment",
    category: "Sales",
    popularity: "Popular",
  },
  {
    id: "template_3",
    name: "Support Triage",
    description: "Triage incoming support emails and create tickets",
    workflow_type: "support_triage",
    category: "Support",
    popularity: "Popular",
  },
  {
    id: "template_4",
    name: "Approval Workflow",
    description: "Route approval requests and chase approvers",
    workflow_type: "approval_workflow",
    category: "Operations",
    popularity: "New",
  },
  {
    id: "template_5",
    name: "Weekly Summary",
    description: "Compile pipeline and project summaries",
    workflow_type: "weekly_summary",
    category: "Management",
    popularity: "New",
  },
];

const workflowCategories = ["All", "Sales", "Support", "Operations", "Management", "Custom"];

export default function WorkflowsPage() {
  const { isLoaded, isSignedIn, user } = useUser();
  const router = useRouter();
  const [workflows, setWorkflows] = useState(mockWorkflows);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [showTemplates, setShowTemplates] = useState(false);

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.push("/login");
    } else if (isLoaded && isSignedIn) {
      // In production, fetch workflows from API
      setTimeout(() => {
        setIsLoading(false);
      }, 1000);
    }
  }, [isLoaded, isSignedIn, router]);

  const getStatusBadge = (status: string, isActive: boolean) => {
    if (!isActive) {
      return <Badge variant="secondary">Inactive</Badge>;
    }
    
    switch (status) {
      case "active":
        return <Badge variant="default">Active</Badge>;
      case "draft":
        return <Badge variant="secondary">Draft</Badge>;
      case "archived":
        return <Badge variant="outline">Archived</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const handleToggleWorkflow = async (workflowId: string, isActive: boolean) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // In production, call API to toggle workflow
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setWorkflows(workflows.map(wf => {
        if (wf.id === workflowId) {
          return {
            ...wf,
            is_active: !isActive,
            status: !isActive ? "active" : "inactive",
          };
        }
        return wf;
      }));
      
      setSuccess(`Workflow ${!isActive ? "enabled" : "disabled"} successfully!`);
    } catch (err) {
      setError("Failed to update workflow. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunWorkflow = async (workflowId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // In production, call API to run workflow
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSuccess("Workflow triggered successfully!");
      
      // Update last run time
      setWorkflows(workflows.map(wf => {
        if (wf.id === workflowId) {
          return {
            ...wf,
            last_run_at: new Date().toISOString(),
            total_runs: wf.total_runs + 1,
          };
        }
        return wf;
      }));
    } catch (err) {
      setError("Failed to run workflow. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteWorkflow = async (workflowId: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // In production, call API to delete workflow
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setWorkflows(workflows.filter(wf => wf.id !== workflowId));
      setSuccess("Workflow deleted successfully!");
    } catch (err) {
      setError("Failed to delete workflow. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateFromTemplate = (templateId: string) => {
    // In production, create workflow from template
    router.push(`/workflows/create?template=${templateId}`);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const filteredWorkflows = selectedCategory === "All" 
    ? workflows 
    : workflows.filter(wf => {
        const template = workflowTemplates.find(t => t.workflow_type === wf.workflow_type);
        return template?.category === selectedCategory;
      });

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
              variant="secondary"
              className="bg-verxlite-neon/20 text-verxlite-neon border-verxlite-neon"
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
          <h1 className="text-3xl font-bold text-gray-900">Workflows</h1>
          <p className="text-gray-600">
            Create and manage automated workflows
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

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setShowTemplates(false)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                !showTemplates
                  ? "border-verxlite-neon text-verxlite-neon"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              My Workflows
            </button>
            <button
              onClick={() => setShowTemplates(true)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                showTemplates
                  ? "border-verxlite-neon text-verxlite-neon"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Templates
            </button>
          </nav>
        </div>

        {/* My Workflows */}
        {!showTemplates ? (
          <div className="space-y-8">
            {/* Filters */}
            <div className="flex flex-wrap gap-2 mb-6">
              {workflowCategories.map((category) => (
                <Button
                  key={category}
                  variant={selectedCategory === category ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedCategory(category)}
                  className={`${
                    selectedCategory === category
                      ? "bg-verxlite-neon text-verxlite-dark"
                      : ""
                  }`}
                >
                  {category}
                </Button>
              ))}
            </div>

            {/* Workflows List */}
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
            ) : filteredWorkflows.length === 0 ? (
              <Card className="text-center py-12">
                <CardHeader>
                  <CardTitle>No Workflows Yet</CardTitle>
                  <CardDescription>
                    Create your first workflow to start automating
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    className="bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90"
                    onClick={() => setShowTemplates(true)}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Create Workflow
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {filteredWorkflows.map((workflow) => {
                  const template = workflowTemplates.find(
                    t => t.workflow_type === workflow.workflow_type
                  );
                  
                  return (
                    <Card key={workflow.id} className="hover:shadow-lg transition-shadow">
                      <CardHeader className="flex flex-row items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className="w-10 h-10 bg-verxlite-neon/20 rounded-lg flex items-center justify-center">
                            <span className="text-verxlite-neon font-bold">
                              {template?.name.charAt(0) || "W"}
                            </span>
                          </div>
                          <div>
                            <CardTitle className="text-xl">{workflow.name}</CardTitle>
                            <CardDescription className="truncate max-w-md">
                              {workflow.description}
                            </CardDescription>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getStatusBadge(workflow.status, workflow.is_active)}
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                          <div>
                            <h3 className="font-medium mb-2">Details</h3>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Type:</span>
                                <span className="capitalize">{workflow.workflow_type}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Priority:</span>
                                <span>{workflow.priority}/10</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Created:</span>
                                <span>{formatDate(workflow.created_at)}</span>
                              </div>
                            </div>
                          </div>
                          <div>
                            <h3 className="font-medium mb-2">Usage</h3>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Total Runs:</span>
                                <span>{workflow.total_runs}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Success Rate:</span>
                                <span>{(workflow.success_rate * 100).toFixed(1)}%</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Last Run:</span>
                                <span>{formatDate(workflow.last_run_at)}</span>
                              </div>
                            </div>
                          </div>
                          <div>
                            <h3 className="font-medium mb-2">Actions</h3>
                            <div className="space-y-2">
                              <Button
                                variant="outline"
                                size="sm"
                                className="w-full justify-start"
                                onClick={() => handleRunWorkflow(workflow.id)}
                                disabled={!workflow.is_active || isLoading}
                              >
                                <Play className="mr-2 h-4 w-4" />
                                Run Now
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                className="w-full justify-start"
                                asChild
                              >
                                <Link href={`/workflows/${workflow.id}`}>
                                  <Eye className="mr-2 h-4 w-4" />
                                  View Details
                                </Link>
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                className="w-full justify-start"
                                asChild
                              >
                                <Link href={`/workflows/${workflow.id}/edit`}>
                                  <Edit className="mr-2 h-4 w-4" />
                                  Edit
                                </Link>
                              </Button>
                              <Button
                                variant="destructive"
                                size="sm"
                                className="w-full justify-start"
                                onClick={() => handleDeleteWorkflow(workflow.id)}
                                disabled={isLoading}
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                              </Button>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                      <CardFooter>
                        <div className="flex items-center space-x-4">
                          <div className="flex items-center space-x-2">
                            <Switch
                              id={`toggle-${workflow.id}`}
                              checked={workflow.is_active}
                              onCheckedChange={() => handleToggleWorkflow(workflow.id, workflow.is_active)}
                              disabled={isLoading}
                            />
                            <Label htmlFor={`toggle-${workflow.id}`}>
                              {workflow.is_active ? "Active" : "Inactive"}
                            </Label>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            asChild
                          >
                            <Link href={`/workflows/${workflow.id}/runs`}>
                              <BarChart3 className="mr-2 h-4 w-4" />
                              View Runs
                            </Link>
                          </Button>
                        </div>
                      </CardFooter>
                    </Card>
                  );
                })}
              </div>
            )}

            {/* Create Workflow Button */}
            <div className="text-center">
              <Button
                className="bg-verxlite-neon text-verxlite-dark hover:bg-verxlite-neon/90"
                onClick={() => setShowTemplates(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Create Workflow
              </Button>
            </div>
          </div>
        ) : (
          // Templates view
          <div className="space-y-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Workflow Templates</h2>
              <Button
                variant="outline"
                onClick={() => setShowTemplates(false)}
              >
                Back to My Workflows
              </Button>
            </div>

            {/* Category Filters */}
            <div className="flex flex-wrap gap-2 mb-6">
              {workflowCategories.map((category) => (
                <Button
                  key={category}
                  variant={selectedCategory === category ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedCategory(category)}
                >
                  {category}
                </Button>
              ))}
            </div>

            {/* Templates Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {workflowTemplates
                .filter(template => selectedCategory === "All" || template.category === selectedCategory)
                .map((template) => (
                  <Card
                    key={template.id}
                    className="hover:shadow-lg transition-shadow cursor-pointer"
                    onClick={() => handleCreateFromTemplate(template.id)}
                  >
                    <CardHeader className="flex flex-row items-center space-x-4">
                      <div className="w-10 h-10 bg-verxlite-neon/20 rounded-lg flex items-center justify-center flex-shrink-0">
                        <span className="text-verxlite-neon font-bold">
                          {template.name.charAt(0)}
                        </span>
                      </div>
                      <div>
                        <CardTitle className="text-lg">{template.name}</CardTitle>
                        <CardDescription className="truncate max-w-xs">
                          {template.description}
                        </CardDescription>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="outline" className="text-xs">
                            {template.category}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            {template.popularity}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Click to create workflow from this template
                        </p>
                      </div>
                    </CardContent>
                    <CardFooter>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full"
                      >
                        Use Template
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
            </div>
          </div>
        )}
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
