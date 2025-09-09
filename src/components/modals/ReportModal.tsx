import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { 
  FileText, 
  Download, 
  CheckCircle, 
  Loader2,
  BarChart3,
  PieChart,
  TrendingUp,
  Calendar,
  Filter,
  Mail
} from "lucide-react";

interface ReportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function ReportModal({ open, onOpenChange }: ReportModalProps) {
  const [reportConfig, setReportConfig] = useState({
    title: "Data Quality Assessment Report",
    description: "Comprehensive analysis of data quality metrics and recommendations",
    timeRange: "30",
    sections: {
      executive_summary: true,
      data_quality_metrics: true,
      issue_analysis: true,
      cleaning_recommendations: true,
      migration_summary: false,
      performance_metrics: true,
      cost_analysis: true
    },
    format: "pdf",
    includeCharts: true,
    includeRawData: false,
    email: "",
    scheduleReport: false
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [reportGenerated, setReportGenerated] = useState(false);

  const updateConfig = (field: string, value: any) => {
    setReportConfig(prev => ({ ...prev, [field]: value }));
  };

  const updateSection = (section: string, enabled: boolean) => {
    setReportConfig(prev => ({
      ...prev,
      sections: { ...prev.sections, [section]: enabled }
    }));
  };

  const generateReport = async () => {
    // Validate required fields
    const enabledSections = Object.values(reportConfig.sections).some(Boolean);
    if (!enabledSections) {
      toast.error('Please select at least one report section');
      return;
    }

    setIsGenerating(true);
    setGenerationProgress(0);
    setReportGenerated(false);

    try {
      // Simulate report generation with progress updates
      const steps = [
        'Collecting data quality metrics...',
        'Analyzing data patterns...',
        'Generating visualizations...',
        'Compiling recommendations...',
        'Creating report document...',
        'Finalizing report...'
      ];

      for (let i = 0; i < steps.length; i++) {
        toast.info(steps[i]);
        await new Promise(resolve => setTimeout(resolve, 1500));
        setGenerationProgress(((i + 1) / steps.length) * 100);
      }

      setReportGenerated(true);
      toast.success('Report generated successfully!', {
        description: `${reportConfig.format.toUpperCase()} report is ready for download`
      });

      // If email is provided, simulate sending
      if (reportConfig.email) {
        setTimeout(() => {
          toast.success(`Report sent to ${reportConfig.email}`);
        }, 1000);
      }

    } catch (error) {
      toast.error('Failed to generate report');
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadReport = () => {
    // Simulate file download
    const link = document.createElement('a');
    link.href = '#'; // In real implementation, this would be the actual file URL
    link.download = `data-quality-report-${Date.now()}.${reportConfig.format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    toast.success('Report downloaded successfully!');
  };

  const sectionOptions = [
    { 
      key: 'executive_summary', 
      label: 'Executive Summary', 
      description: 'High-level overview and key findings',
      icon: FileText 
    },
    { 
      key: 'data_quality_metrics', 
      label: 'Data Quality Metrics', 
      description: 'Completeness, accuracy, consistency scores',
      icon: BarChart3 
    },
    { 
      key: 'issue_analysis', 
      label: 'Issue Analysis', 
      description: 'Detailed breakdown of data quality issues',
      icon: PieChart 
    },
    { 
      key: 'cleaning_recommendations', 
      label: 'Cleaning Recommendations', 
      description: 'AI-powered suggestions for data improvement',
      icon: CheckCircle 
    },
    { 
      key: 'migration_summary', 
      label: 'Migration Summary', 
      description: 'Database migration status and results',
      icon: TrendingUp 
    },
    { 
      key: 'performance_metrics', 
      label: 'Performance Metrics', 
      description: 'Processing times and system performance',
      icon: TrendingUp 
    },
    { 
      key: 'cost_analysis', 
      label: 'Cost Analysis', 
      description: 'Cost savings and ROI calculations',
      icon: TrendingUp 
    }
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <FileText className="h-5 w-5 mr-2" />
            Generate Comprehensive Report
          </DialogTitle>
          <DialogDescription>
            Create detailed analysis reports with customizable sections and formats
          </DialogDescription>
        </DialogHeader>

        {!reportGenerated ? (
          <div className="space-y-6">
            {/* Report Details */}
            <div className="space-y-4">
              <div>
                <Label htmlFor="report-title">Report Title</Label>
                <Input
                  id="report-title"
                  value={reportConfig.title}
                  onChange={(e) => updateConfig('title', e.target.value)}
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="report-description">Description</Label>
                <Textarea
                  id="report-description"
                  value={reportConfig.description}
                  onChange={(e) => updateConfig('description', e.target.value)}
                  className="mt-1"
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="time-range">Time Range</Label>
                  <Select 
                    value={reportConfig.timeRange} 
                    onValueChange={(value) => updateConfig('timeRange', value)}
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="7">Last 7 days</SelectItem>
                      <SelectItem value="30">Last 30 days</SelectItem>
                      <SelectItem value="90">Last 90 days</SelectItem>
                      <SelectItem value="365">Last year</SelectItem>
                      <SelectItem value="all">All time</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="format">Format</Label>
                  <Select 
                    value={reportConfig.format} 
                    onValueChange={(value) => updateConfig('format', value)}
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pdf">PDF Document</SelectItem>
                      <SelectItem value="xlsx">Excel Spreadsheet</SelectItem>
                      <SelectItem value="html">HTML Report</SelectItem>
                      <SelectItem value="csv">CSV Data</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Report Sections */}
            <div className="space-y-4">
              <h4 className="font-medium flex items-center">
                <Filter className="h-4 w-4 mr-2" />
                Report Sections
              </h4>
              <div className="grid grid-cols-1 gap-3">
                {sectionOptions.map((section) => (
                  <div 
                    key={section.key}
                    className="flex items-start space-x-3 p-3 rounded-lg border border-border/50 hover:bg-muted/30 transition-colors"
                  >
                    <Checkbox
                      id={section.key}
                      checked={reportConfig.sections[section.key as keyof typeof reportConfig.sections]}
                      onCheckedChange={(checked) => updateSection(section.key, !!checked)}
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <section.icon className="h-4 w-4 text-muted-foreground" />
                        <Label htmlFor={section.key} className="font-medium cursor-pointer">
                          {section.label}
                        </Label>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {section.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Additional Options */}
            <div className="space-y-4">
              <h4 className="font-medium">Additional Options</h4>
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="includeCharts"
                    checked={reportConfig.includeCharts}
                    onCheckedChange={(checked) => updateConfig('includeCharts', !!checked)}
                  />
                  <Label htmlFor="includeCharts" className="text-sm">
                    Include charts and visualizations
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="includeRawData"
                    checked={reportConfig.includeRawData}
                    onCheckedChange={(checked) => updateConfig('includeRawData', !!checked)}
                  />
                  <Label htmlFor="includeRawData" className="text-sm">
                    Include raw data tables
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="scheduleReport"
                    checked={reportConfig.scheduleReport}
                    onCheckedChange={(checked) => updateConfig('scheduleReport', !!checked)}
                  />
                  <Label htmlFor="scheduleReport" className="text-sm">
                    Schedule regular report generation
                  </Label>
                </div>
              </div>

              <div>
                <Label htmlFor="email">Email Report To (Optional)</Label>
                <div className="flex items-center space-x-2 mt-1">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    value={reportConfig.email}
                    onChange={(e) => updateConfig('email', e.target.value)}
                    placeholder="user@company.com"
                    className="flex-1"
                  />
                </div>
              </div>
            </div>

            {/* Generation Progress */}
            {isGenerating && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Generating Report...</span>
                  <span className="text-sm text-muted-foreground">{Math.round(generationProgress)}%</span>
                </div>
                <Progress value={generationProgress} className="h-2" />
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end space-x-2 pt-4 border-t">
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isGenerating}
              >
                Cancel
              </Button>
              <Button
                onClick={generateReport}
                disabled={isGenerating}
                className="min-w-[140px]"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FileText className="h-4 w-4 mr-2" />
                    Generate Report
                  </>
                )}
              </Button>
            </div>
          </div>
        ) : (
          /* Report Generated Success State */
          <div className="text-center py-8 space-y-6">
            <div className="space-y-4">
              <CheckCircle className="h-16 w-16 mx-auto text-success" />
              <div>
                <h3 className="text-xl font-semibold mb-2">Report Generated Successfully!</h3>
                <p className="text-muted-foreground">
                  Your comprehensive data quality report is ready
                </p>
              </div>
            </div>

            <div className="bg-muted/50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span>Report Title:</span>
                <span className="font-medium">{reportConfig.title}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Format:</span>
                <Badge variant="outline">{reportConfig.format.toUpperCase()}</Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span>Time Range:</span>
                <span>Last {reportConfig.timeRange} days</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Sections:</span>
                <span>{Object.values(reportConfig.sections).filter(Boolean).length} sections</span>
              </div>
            </div>

            <div className="flex justify-center space-x-3">
              <Button variant="outline" onClick={() => {
                setReportGenerated(false);
                setGenerationProgress(0);
              }}>
                Generate Another
              </Button>
              <Button onClick={downloadReport}>
                <Download className="h-4 w-4 mr-2" />
                Download Report
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}