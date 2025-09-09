import { useState, useRef } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { 
  Upload, 
  FileText, 
  X, 
  CheckCircle, 
  AlertTriangle,
  Loader2,
  Settings,
  Play
} from "lucide-react";
import { useFileUpload } from "@/hooks/useApi";

interface FileUploadModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function FileUploadModal({ open, onOpenChange }: FileUploadModalProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({});
  const [uploadOptions, setUploadOptions] = useState({
    autoAnalyze: true,
    detectDuplicates: true,
    validateSchema: true,
    generateReport: true
  });
  const [activeTab, setActiveTab] = useState("upload");
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const fileUploadMutation = useFileUpload();

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setSelectedFiles(prev => [...prev, ...files]);
  };

  const handleFileDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    setSelectedFiles(prev => [...prev, ...files]);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFile = async (file: File) => {
    const fileId = `${file.name}-${Date.now()}`;
    
    try {
      // Simulate upload progress
      setUploadProgress(prev => ({ ...prev, [fileId]: 0 }));
      
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          const currentProgress = prev[fileId] || 0;
          if (currentProgress >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return { ...prev, [fileId]: currentProgress + 10 };
        });
      }, 200);

      const result = await fileUploadMutation.mutateAsync({ 
        file,
        options: uploadOptions
      });

      clearInterval(progressInterval);
      setUploadProgress(prev => ({ ...prev, [fileId]: 100 }));
      
      if (result.data) {
        toast.success(`${file.name} uploaded successfully!`, {
          description: uploadOptions.autoAnalyze ? 'Analysis started automatically' : 'File ready for analysis'
        });
        
        // Move to results tab after successful upload
        setTimeout(() => setActiveTab("results"), 1000);
      }
      
      return result;
    } catch (error) {
      toast.error(`Failed to upload ${file.name}`);
      setUploadProgress(prev => {
        const newProgress = { ...prev };
        delete newProgress[fileId];
        return newProgress;
      });
      throw error;
    }
  };

  const uploadAllFiles = async () => {
    if (selectedFiles.length === 0) {
      toast.error('Please select at least one file');
      return;
    }

    try {
      const uploadPromises = selectedFiles.map(file => uploadFile(file));
      await Promise.all(uploadPromises);
      
      toast.success('All files uploaded successfully!', {
        description: `${selectedFiles.length} files processed`
      });
      
      // Clear files after successful upload
      setTimeout(() => {
        setSelectedFiles([]);
        setUploadProgress({});
      }, 2000);
      
    } catch (error) {
      toast.error('Some uploads failed. Please try again.');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <Upload className="h-5 w-5 mr-2" />
            Upload Data Files
          </DialogTitle>
          <DialogDescription>
            Upload your data files for quality analysis and cleaning
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="upload">Upload Files</TabsTrigger>
            <TabsTrigger value="options">Upload Options</TabsTrigger>
            <TabsTrigger value="results">Results</TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-4">
            {/* File Drop Zone */}
            <div 
              className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition-colors cursor-pointer"
              onDrop={handleFileDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-medium mb-2">Drop files here or click to browse</h3>
              <p className="text-muted-foreground mb-4">
                Supports CSV, Excel, JSON, TSV, and Parquet files up to 500MB each
              </p>
              <Button variant="outline">
                <FileText className="h-4 w-4 mr-2" />
                Select Files
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".csv,.xlsx,.xls,.json,.tsv,.parquet"
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>

            {/* Selected Files List */}
            {selectedFiles.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-medium">Selected Files ({selectedFiles.length})</h4>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {selectedFiles.map((file, index) => {
                    const fileId = `${file.name}-${Date.now()}`;
                    const progress = uploadProgress[fileId] || 0;
                    
                    return (
                      <div key={`${file.name}-${index}`} className="flex items-center justify-between p-3 rounded-lg border border-border/50">
                        <div className="flex items-center space-x-3 flex-1">
                          <FileText className="h-5 w-5 text-muted-foreground" />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{file.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {formatFileSize(file.size)} • {file.type || 'Unknown type'}
                            </p>
                            {progress > 0 && (
                              <div className="mt-2">
                                <Progress value={progress} className="h-2" />
                                <p className="text-xs text-muted-foreground mt-1">{progress}% uploaded</p>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {progress === 100 && (
                            <CheckCircle className="h-4 w-4 text-success" />
                          )}
                          {progress > 0 && progress < 100 && (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              removeFile(index);
                            }}
                            disabled={progress > 0 && progress < 100}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
                
                <div className="flex justify-end space-x-2">
                  <Button
                    variant="outline"
                    onClick={() => setSelectedFiles([])}
                    disabled={fileUploadMutation.isPending}
                  >
                    Clear All
                  </Button>
                  <Button
                    onClick={uploadAllFiles}
                    disabled={fileUploadMutation.isPending || selectedFiles.length === 0}
                    className="min-w-[120px]"
                  >
                    {fileUploadMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload All
                      </>
                    )}
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="options" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-medium flex items-center">
                  <Settings className="h-4 w-4 mr-2" />
                  Analysis Options
                </h4>
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="autoAnalyze"
                      checked={uploadOptions.autoAnalyze}
                      onCheckedChange={(checked) => 
                        setUploadOptions(prev => ({ ...prev, autoAnalyze: !!checked }))
                      }
                    />
                    <Label htmlFor="autoAnalyze" className="text-sm">
                      Start analysis automatically after upload
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="detectDuplicates"
                      checked={uploadOptions.detectDuplicates}
                      onCheckedChange={(checked) => 
                        setUploadOptions(prev => ({ ...prev, detectDuplicates: !!checked }))
                      }
                    />
                    <Label htmlFor="detectDuplicates" className="text-sm">
                      Detect duplicate records
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="validateSchema"
                      checked={uploadOptions.validateSchema}
                      onCheckedChange={(checked) => 
                        setUploadOptions(prev => ({ ...prev, validateSchema: !!checked }))
                      }
                    />
                    <Label htmlFor="validateSchema" className="text-sm">
                      Validate data schema and types
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="generateReport"
                      checked={uploadOptions.generateReport}
                      onCheckedChange={(checked) => 
                        setUploadOptions(prev => ({ ...prev, generateReport: !!checked }))
                      }
                    />
                    <Label htmlFor="generateReport" className="text-sm">
                      Generate quality assessment report
                    </Label>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium">Processing Options</h4>
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="sampleSize" className="text-sm">Sample Size for Analysis</Label>
                    <Select defaultValue="full">
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1000">1,000 rows</SelectItem>
                        <SelectItem value="10000">10,000 rows</SelectItem>
                        <SelectItem value="100000">100,000 rows</SelectItem>
                        <SelectItem value="full">Full dataset</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="confidenceLevel" className="text-sm">Confidence Threshold</Label>
                    <Select defaultValue="85">
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="70">70% - Fast</SelectItem>
                        <SelectItem value="85">85% - Balanced</SelectItem>
                        <SelectItem value="95">95% - Thorough</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="results" className="space-y-4">
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 mx-auto mb-4 text-success" />
              <h3 className="text-lg font-medium mb-2">Upload Complete!</h3>
              <p className="text-muted-foreground mb-4">
                Your files have been uploaded and analysis is in progress.
              </p>
              <div className="flex justify-center space-x-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    onOpenChange(false);
                    // Navigate to data quality page to see results
                    window.location.hash = '#/data-quality';
                  }}
                >
                  View Analysis Results
                </Button>
                <Button
                  onClick={() => {
                    setSelectedFiles([]);
                    setUploadProgress({});
                    setActiveTab("upload");
                  }}
                >
                  Upload More Files
                </Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}