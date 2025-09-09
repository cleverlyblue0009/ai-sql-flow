import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { 
  Settings, 
  Play, 
  CheckCircle, 
  Loader2,
  AlertTriangle,
  TrendingUp,
  Database,
  Zap,
  BarChart3,
  RefreshCw
} from "lucide-react";
import { useStartCleaning } from "@/hooks/useApi";

interface DataCleaningModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  fileId?: string;
  fileName?: string;
}

export default function DataCleaningModal({ 
  open, 
  onOpenChange, 
  fileId = "sample_file", 
  fileName = "customer_data.csv" 
}: DataCleaningModalProps) {
  const [cleaningConfig, setCleaningConfig] = useState({
    duplicates: {
      enabled: true,
      strategy: "exact_match",
      threshold: 95
    },
    missingValues: {
      enabled: true,
      strategy: "ml_prediction",
      threshold: 80
    },
    outliers: {
      enabled: true,
      strategy: "isolation_forest",
      threshold: 85
    },
    formatting: {
      enabled: true,
      standardizeText: true,
      normalizeDates: true,
      validateEmails: true
    },
    validation: {
      enabled: true,
      schemaValidation: true,
      dataTypeValidation: true,
      constraintValidation: true
    }
  });
  
  const [cleaningProgress, setCleaningProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState("");
  const [cleaningResults, setCleaningResults] = useState<any>(null);
  
  const startCleaningMutation = useStartCleaning();

  const updateConfig = (section: string, field: string, value: any) => {
    setCleaningConfig(prev => ({
      ...prev,
      [section]: { ...prev[section as keyof typeof prev], [field]: value }
    }));
  };

  const startCleaning = async () => {
    setIsProcessing(true);
    setCleaningProgress(0);
    setCleaningResults(null);

    const steps = [
      { name: "Analyzing data structure...", duration: 2000 },
      { name: "Detecting duplicates...", duration: 3000 },
      { name: "Processing missing values...", duration: 2500 },
      { name: "Identifying outliers...", duration: 2000 },
      { name: "Standardizing formats...", duration: 1500 },
      { name: "Validating data quality...", duration: 2000 },
      { name: "Generating recommendations...", duration: 1000 }
    ];

    try {
      for (let i = 0; i < steps.length; i++) {
        setProcessingStep(steps[i].name);
        await new Promise(resolve => setTimeout(resolve, steps[i].duration));
        setCleaningProgress(((i + 1) / steps.length) * 100);
      }

      // Simulate cleaning results
      const results = {
        recordsProcessed: 124789,
        duplicatesRemoved: 2847,
        missingValuesFixed: 1923,
        outliersHandled: 456,
        formatIssuesFixed: 3421,
        qualityImprovement: 23.7,
        processingTime: "4 minutes 32 seconds",
        recommendations: [
          "Consider implementing data validation at source",
          "Review duplicate detection rules for customer records",
          "Add constraints to prevent future data quality issues"
        ]
      };

      setCleaningResults(results);
      
      toast.success('Data cleaning completed successfully!', {
        description: `Processed ${results.recordsProcessed.toLocaleString()} records with ${results.qualityImprovement}% quality improvement`
      });

    } catch (error) {
      toast.error('Cleaning process failed');
    } finally {
      setIsProcessing(false);
      setProcessingStep("");
    }
  };

  const previewChanges = () => {
    toast.info('Generating preview...', {
      description: 'This would show a sample of proposed changes'
    });
    
    // Simulate preview generation
    setTimeout(() => {
      toast.success('Preview ready!', {
        description: 'Review the proposed changes in the preview tab'
      });
    }, 2000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <Settings className="h-5 w-5 mr-2" />
            Data Cleaning Configuration
          </DialogTitle>
          <DialogDescription>
            Configure AI-powered cleaning operations for {fileName}
          </DialogDescription>
        </DialogHeader>

        {!cleaningResults ? (
          <Tabs defaultValue="duplicates" className="w-full">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="duplicates">Duplicates</TabsTrigger>
              <TabsTrigger value="missing">Missing Values</TabsTrigger>
              <TabsTrigger value="outliers">Outliers</TabsTrigger>
              <TabsTrigger value="formatting">Formatting</TabsTrigger>
              <TabsTrigger value="validation">Validation</TabsTrigger>
            </TabsList>

            <TabsContent value="duplicates" className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <Checkbox
                  id="duplicates-enabled"
                  checked={cleaningConfig.duplicates.enabled}
                  onCheckedChange={(checked) => updateConfig('duplicates', 'enabled', !!checked)}
                />
                <Label htmlFor="duplicates-enabled" className="font-medium">
                  Enable duplicate detection and removal
                </Label>
              </div>

              <div className="space-y-4">
                <div>
                  <Label>Detection Strategy</Label>
                  <Select 
                    value={cleaningConfig.duplicates.strategy} 
                    onValueChange={(value) => updateConfig('duplicates', 'strategy', value)}
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="exact_match">Exact Match</SelectItem>
                      <SelectItem value="fuzzy_match">Fuzzy Match</SelectItem>
                      <SelectItem value="semantic_match">AI Semantic Match</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Similarity Threshold: {cleaningConfig.duplicates.threshold}%</Label>
                  <div className="mt-2">
                    <input
                      type="range"
                      min="50"
                      max="100"
                      value={cleaningConfig.duplicates.threshold}
                      onChange={(e) => updateConfig('duplicates', 'threshold', parseInt(e.target.value))}
                      className="w-full"
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>Lenient (50%)</span>
                    <span>Strict (100%)</span>
                  </div>
                </div>

                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    <strong>Current setting:</strong> {cleaningConfig.duplicates.strategy === 'exact_match' ? 'Exact match' : 
                    cleaningConfig.duplicates.strategy === 'fuzzy_match' ? 'Fuzzy matching' : 'AI semantic matching'} 
                    with {cleaningConfig.duplicates.threshold}% similarity threshold.
                  </p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="missing" className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <Checkbox
                  id="missing-enabled"
                  checked={cleaningConfig.missingValues.enabled}
                  onCheckedChange={(checked) => updateConfig('missingValues', 'enabled', !!checked)}
                />
                <Label htmlFor="missing-enabled" className="font-medium">
                  Enable missing value imputation
                </Label>
              </div>

              <div className="space-y-4">
                <div>
                  <Label>Imputation Strategy</Label>
                  <Select 
                    value={cleaningConfig.missingValues.strategy} 
                    onValueChange={(value) => updateConfig('missingValues', 'strategy', value)}
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="mean_median">Mean/Median</SelectItem>
                      <SelectItem value="forward_fill">Forward Fill</SelectItem>
                      <SelectItem value="ml_prediction">ML Prediction</SelectItem>
                      <SelectItem value="remove_rows">Remove Rows</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Confidence Threshold: {cleaningConfig.missingValues.threshold}%</Label>
                  <div className="mt-2">
                    <input
                      type="range"
                      min="60"
                      max="95"
                      value={cleaningConfig.missingValues.threshold}
                      onChange={(e) => updateConfig('missingValues', 'threshold', parseInt(e.target.value))}
                      className="w-full"
                    />
                  </div>
                </div>

                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    <strong>Strategy:</strong> {cleaningConfig.missingValues.strategy === 'ml_prediction' ? 
                    'Use machine learning to predict missing values based on other columns' :
                    cleaningConfig.missingValues.strategy === 'mean_median' ? 
                    'Fill with statistical measures (mean for numeric, mode for categorical)' :
                    cleaningConfig.missingValues.strategy === 'forward_fill' ?
                    'Use the last known value to fill gaps' :
                    'Remove rows with missing values'}
                  </p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="outliers" className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <Checkbox
                  id="outliers-enabled"
                  checked={cleaningConfig.outliers.enabled}
                  onCheckedChange={(checked) => updateConfig('outliers', 'enabled', !!checked)}
                />
                <Label htmlFor="outliers-enabled" className="font-medium">
                  Enable outlier detection and handling
                </Label>
              </div>

              <div className="space-y-4">
                <div>
                  <Label>Detection Method</Label>
                  <Select 
                    value={cleaningConfig.outliers.strategy} 
                    onValueChange={(value) => updateConfig('outliers', 'strategy', value)}
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="isolation_forest">Isolation Forest (AI)</SelectItem>
                      <SelectItem value="z_score">Z-Score Method</SelectItem>
                      <SelectItem value="iqr">Interquartile Range</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Detection Sensitivity: {cleaningConfig.outliers.threshold}%</Label>
                  <div className="mt-2">
                    <input
                      type="range"
                      min="70"
                      max="95"
                      value={cleaningConfig.outliers.threshold}
                      onChange={(e) => updateConfig('outliers', 'threshold', parseInt(e.target.value))}
                      className="w-full"
                    />
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="formatting" className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <Checkbox
                  id="formatting-enabled"
                  checked={cleaningConfig.formatting.enabled}
                  onCheckedChange={(checked) => updateConfig('formatting', 'enabled', !!checked)}
                />
                <Label htmlFor="formatting-enabled" className="font-medium">
                  Enable format standardization
                </Label>
              </div>

              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="standardize-text"
                    checked={cleaningConfig.formatting.standardizeText}
                    onCheckedChange={(checked) => updateConfig('formatting', 'standardizeText', !!checked)}
                  />
                  <Label htmlFor="standardize-text" className="text-sm">
                    Standardize text case and whitespace
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="normalize-dates"
                    checked={cleaningConfig.formatting.normalizeDates}
                    onCheckedChange={(checked) => updateConfig('formatting', 'normalizeDates', !!checked)}
                  />
                  <Label htmlFor="normalize-dates" className="text-sm">
                    Normalize date formats
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="validate-emails"
                    checked={cleaningConfig.formatting.validateEmails}
                    onCheckedChange={(checked) => updateConfig('formatting', 'validateEmails', !!checked)}
                  />
                  <Label htmlFor="validate-emails" className="text-sm">
                    Validate and format email addresses
                  </Label>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="validation" className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <Checkbox
                  id="validation-enabled"
                  checked={cleaningConfig.validation.enabled}
                  onCheckedChange={(checked) => updateConfig('validation', 'enabled', !!checked)}
                />
                <Label htmlFor="validation-enabled" className="font-medium">
                  Enable data validation
                </Label>
              </div>

              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="schema-validation"
                    checked={cleaningConfig.validation.schemaValidation}
                    onCheckedChange={(checked) => updateConfig('validation', 'schemaValidation', !!checked)}
                  />
                  <Label htmlFor="schema-validation" className="text-sm">
                    Validate against expected schema
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="datatype-validation"
                    checked={cleaningConfig.validation.dataTypeValidation}
                    onCheckedChange={(checked) => updateConfig('validation', 'dataTypeValidation', !!checked)}
                  />
                  <Label htmlFor="datatype-validation" className="text-sm">
                    Validate data types and formats
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="constraint-validation"
                    checked={cleaningConfig.validation.constraintValidation}
                    onCheckedChange={(checked) => updateConfig('validation', 'constraintValidation', !!checked)}
                  />
                  <Label htmlFor="constraint-validation" className="text-sm">
                    Validate business rule constraints
                  </Label>
                </div>
              </div>
            </TabsContent>

            {/* Processing Progress */}
            {isProcessing && (
              <div className="mt-6 p-4 bg-muted/50 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-medium">Processing Data...</span>
                  <span className="text-sm text-muted-foreground">{Math.round(cleaningProgress)}%</span>
                </div>
                <Progress value={cleaningProgress} className="h-2 mb-2" />
                <div className="flex items-center text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {processingStep}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end space-x-2 pt-4 border-t">
              <Button
                variant="outline"
                onClick={previewChanges}
                disabled={isProcessing}
              >
                <Play className="h-4 w-4 mr-2" />
                Preview Changes
              </Button>
              <Button
                onClick={startCleaning}
                disabled={isProcessing}
                className="min-w-[160px]"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Start Cleaning
                  </>
                )}
              </Button>
            </div>
          </Tabs>
        ) : (
          /* Cleaning Results */
          <div className="space-y-6">
            <div className="text-center">
              <CheckCircle className="h-16 w-16 mx-auto mb-4 text-success" />
              <h3 className="text-xl font-semibold mb-2">Data Cleaning Complete!</h3>
              <p className="text-muted-foreground">
                Your data has been successfully cleaned and optimized
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <BarChart3 className="h-8 w-8 mx-auto mb-2 text-primary" />
                <div className="text-2xl font-bold">{cleaningResults.recordsProcessed.toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Records Processed</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <Database className="h-8 w-8 mx-auto mb-2 text-success" />
                <div className="text-2xl font-bold">{cleaningResults.duplicatesRemoved.toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Duplicates Removed</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <TrendingUp className="h-8 w-8 mx-auto mb-2 text-warning" />
                <div className="text-2xl font-bold">{cleaningResults.missingValuesFixed.toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Missing Values Fixed</div>
              </div>
              <div className="text-center p-4 bg-muted/50 rounded-lg">
                <Zap className="h-8 w-8 mx-auto mb-2 text-success" />
                <div className="text-2xl font-bold">+{cleaningResults.qualityImprovement}%</div>
                <div className="text-sm text-muted-foreground">Quality Improvement</div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="font-medium">Recommendations for Future Data Quality</h4>
              <div className="space-y-2">
                {cleaningResults.recommendations.map((rec: string, index: number) => (
                  <div key={index} className="flex items-start space-x-2">
                    <CheckCircle className="h-4 w-4 text-success mt-0.5" />
                    <span className="text-sm">{rec}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-center space-x-3">
              <Button 
                variant="outline" 
                onClick={() => {
                  setCleaningResults(null);
                  setCleaningProgress(0);
                }}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Clean Another File
              </Button>
              <Button onClick={() => onOpenChange(false)}>
                View Cleaned Data
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}