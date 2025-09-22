import { BatchTranslationResult, TranslationResult } from './sqlTranslationEngine';
import { SQLFile } from '@/components/MultiFileSQLInput';

export interface DownloadOptions {
  includeOriginal: boolean;
  includeReport: boolean;
  includeMetadata: boolean;
  format: 'zip' | 'tar' | 'individual';
  compression: 'none' | 'gzip';
}

export interface FileDownload {
  name: string;
  content: string;
  type: 'sql' | 'txt' | 'md' | 'json';
  size: number;
}

export class DownloadSystem {
  // Generate migration report
  static generateMigrationReport(
    batchResult: BatchTranslationResult,
    sourceDialect: string,
    targetDialect: string,
    jobName: string
  ): string {
    const timestamp = new Date().toISOString();
    const totalFiles = batchResult.files.length;
    const totalWarnings = batchResult.files.reduce((sum, f) => sum + f.result.warnings.length, 0);
    const totalErrors = batchResult.files.reduce((sum, f) => sum + f.result.errors.length, 0);
    const avgConfidence = Math.round(
      batchResult.files.reduce((sum, f) => sum + f.result.confidence, 0) / totalFiles
    );

    return `# SQL Migration Report

## Job Information
- **Job Name**: ${jobName}
- **Generated**: ${new Date(timestamp).toLocaleString()}
- **Source Dialect**: ${sourceDialect.toUpperCase()}
- **Target Dialect**: ${targetDialect.toUpperCase()}
- **Migration Engine**: DataFlow AI SQL Translation Engine v2.0

## Summary
- **Files Processed**: ${totalFiles}
- **Total Warnings**: ${totalWarnings}
- **Total Errors**: ${totalErrors}
- **Average Confidence**: ${avgConfidence}%
- **Estimated Execution Time**: ${batchResult.estimatedExecutionTime}

## Execution Order
The files should be executed in the following order to respect dependencies:

${batchResult.dependencyOrder.map((fileName, index) => `${index + 1}. ${fileName}`).join('\n')}

## File Details

${batchResult.files.map(file => `
### ${file.name}
- **Translation Confidence**: ${file.result.confidence}%
- **Rules Applied**: ${file.result.appliedRules.length}
- **Warnings**: ${file.result.warnings.length}
- **Errors**: ${file.result.errors.length}
- **Unsupported Features**: ${file.result.unsupportedFeatures.length}

${file.result.appliedRules.length > 0 ? `
#### Applied Transformation Rules
${file.result.appliedRules.map(rule => `- **${rule.description}**: ${rule.matches} occurrence(s)`).join('\n')}
` : ''}

${file.result.warnings.length > 0 ? `
#### Warnings
${file.result.warnings.map(warning => `- ⚠️ ${warning}`).join('\n')}
` : ''}

${file.result.errors.length > 0 ? `
#### Errors
${file.result.errors.map(error => `- ❌ ${error}`).join('\n')}
` : ''}

${file.result.unsupportedFeatures.length > 0 ? `
#### Unsupported Features
${file.result.unsupportedFeatures.map(feature => `- 🚫 ${feature}`).join('\n')}
` : ''}
`).join('\n')}

${batchResult.globalWarnings.length > 0 ? `
## Global Warnings
${batchResult.globalWarnings.map(warning => `- ⚠️ ${warning}`).join('\n')}
` : ''}

## Recommendations

### Pre-Execution Checklist
- [ ] Review all warnings and errors listed above
- [ ] Backup your target database before executing the migration
- [ ] Test the migration on a development environment first
- [ ] Verify that all dependencies are properly ordered
- [ ] Check for unsupported features and implement alternatives

### Post-Migration Validation
- [ ] Verify data integrity after migration
- [ ] Run performance tests on critical queries
- [ ] Update application connection strings and configurations
- [ ] Monitor query performance and optimize as needed
- [ ] Update documentation and schema diagrams

### Performance Optimization Tips
- Create indexes on frequently queried columns
- Update table statistics after data migration
- Consider partitioning for large tables
- Review and optimize query plans
- Monitor resource usage and scale as needed

---
*This report was generated automatically by DataFlow AI SQL Migration Tool. Please review all recommendations before proceeding with the migration.*`;
  }

  // Generate metadata file
  static generateMetadata(
    batchResult: BatchTranslationResult,
    sourceDialect: string,
    targetDialect: string,
    options: DownloadOptions
  ): string {
    const metadata = {
      migration: {
        timestamp: new Date().toISOString(),
        sourceDialect,
        targetDialect,
        engine: 'DataFlow AI SQL Translation Engine v2.0',
        version: '2.0.0'
      },
      summary: {
        filesProcessed: batchResult.files.length,
        totalWarnings: batchResult.files.reduce((sum, f) => sum + f.result.warnings.length, 0),
        totalErrors: batchResult.files.reduce((sum, f) => sum + f.result.errors.length, 0),
        averageConfidence: Math.round(
          batchResult.files.reduce((sum, f) => sum + f.result.confidence, 0) / batchResult.files.length
        ),
        estimatedExecutionTime: batchResult.estimatedExecutionTime
      },
      executionOrder: batchResult.dependencyOrder,
      files: batchResult.files.map(file => ({
        id: file.id,
        name: file.name,
        confidence: file.result.confidence,
        rulesApplied: file.result.appliedRules.length,
        warnings: file.result.warnings.length,
        errors: file.result.errors.length,
        unsupportedFeatures: file.result.unsupportedFeatures.length,
        transformationRules: file.result.appliedRules.map(rule => ({
          description: rule.description,
          matches: rule.matches
        }))
      })),
      globalWarnings: batchResult.globalWarnings,
      downloadOptions: options
    };

    return JSON.stringify(metadata, null, 2);
  }

  // Create individual file downloads
  static createFileDownloads(
    batchResult: BatchTranslationResult,
    originalFiles: SQLFile[],
    sourceDialect: string,
    targetDialect: string,
    jobName: string,
    options: DownloadOptions
  ): FileDownload[] {
    const downloads: FileDownload[] = [];

    // Add translated SQL files
    batchResult.files.forEach(file => {
      const translatedFile: FileDownload = {
        name: `translated_${file.name}`,
        content: file.result.translatedContent,
        type: 'sql',
        size: file.result.translatedContent.length
      };
      downloads.push(translatedFile);

      // Add original files if requested
      if (options.includeOriginal) {
        const originalFile = originalFiles.find(f => f.id === file.id);
        if (originalFile) {
          const originalDownload: FileDownload = {
            name: `original_${file.name}`,
            content: originalFile.content,
            type: 'sql',
            size: originalFile.content.length
          };
          downloads.push(originalDownload);
        }
      }
    });

    // Add migration report if requested
    if (options.includeReport) {
      const report = this.generateMigrationReport(batchResult, sourceDialect, targetDialect, jobName);
      const reportFile: FileDownload = {
        name: 'MIGRATION_REPORT.md',
        content: report,
        type: 'md',
        size: report.length
      };
      downloads.push(reportFile);
    }

    // Add metadata if requested
    if (options.includeMetadata) {
      const metadata = this.generateMetadata(batchResult, sourceDialect, targetDialect, options);
      const metadataFile: FileDownload = {
        name: 'migration_metadata.json',
        content: metadata,
        type: 'json',
        size: metadata.length
      };
      downloads.push(metadataFile);
    }

    // Add execution script
    const executionScript = this.generateExecutionScript(batchResult, targetDialect);
    const scriptFile: FileDownload = {
      name: `execute_migration_${targetDialect}.sql`,
      content: executionScript,
      type: 'sql',
      size: executionScript.length
    };
    downloads.push(scriptFile);

    return downloads;
  }

  // Generate execution script
  static generateExecutionScript(batchResult: BatchTranslationResult, targetDialect: string): string {
    const header = `-- ${targetDialect.toUpperCase()} Migration Execution Script
-- Generated: ${new Date().toISOString()}
-- Execute files in the order specified below

-- IMPORTANT: Review all files before execution
-- IMPORTANT: Backup your database before running this script

SET AUTOCOMMIT = 0;
START TRANSACTION;

`;

    const fileExecutions = batchResult.dependencyOrder.map((fileName, index) => {
      return `
-- Step ${index + 1}: Execute ${fileName}
-- File: translated_${fileName}
-- Review the file content before uncommenting the next line
-- SOURCE translated_${fileName};

`;
    }).join('');

    const footer = `
-- Commit the transaction if all steps completed successfully
-- COMMIT;

-- If there were errors, rollback the transaction
-- ROLLBACK;

-- Post-migration validation queries
-- Add your validation queries here
-- SELECT COUNT(*) FROM your_tables;
-- SHOW TABLES;
-- DESCRIBE your_key_tables;
`;

    return header + fileExecutions + footer;
  }

  // Download single file
  static downloadFile(file: FileDownload): void {
    const mimeTypes = {
      sql: 'text/sql',
      txt: 'text/plain',
      md: 'text/markdown',
      json: 'application/json'
    };

    const blob = new Blob([file.content], { type: mimeTypes[file.type] });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Download multiple files as zip (simplified - creates a combined file)
  static downloadAsZip(
    files: FileDownload[],
    zipName: string,
    options: DownloadOptions
  ): void {
    let zipContent = `# ${zipName}\n# Generated: ${new Date().toISOString()}\n\n`;
    
    // Add table of contents
    zipContent += `## Table of Contents\n\n`;
    files.forEach((file, index) => {
      zipContent += `${index + 1}. ${file.name} (${file.type.toUpperCase()}, ${(file.size / 1024).toFixed(1)} KB)\n`;
    });
    zipContent += '\n';

    // Add files with separators
    files.forEach(file => {
      zipContent += `\n${'='.repeat(80)}\n`;
      zipContent += `FILE: ${file.name}\n`;
      zipContent += `TYPE: ${file.type.toUpperCase()}\n`;
      zipContent += `SIZE: ${(file.size / 1024).toFixed(1)} KB\n`;
      zipContent += `${'='.repeat(80)}\n\n`;
      zipContent += file.content;
      zipContent += '\n\n';
    });

    // Add footer
    zipContent += `\n${'='.repeat(80)}\n`;
    zipContent += `END OF ARCHIVE\n`;
    zipContent += `Files: ${files.length}\n`;
    zipContent += `Total Size: ${(zipContent.length / 1024).toFixed(1)} KB\n`;
    zipContent += `Generated: ${new Date().toISOString()}\n`;
    zipContent += `${'='.repeat(80)}\n`;

    const blob = new Blob([zipContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${zipName}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Get download size estimate
  static getDownloadSizeEstimate(files: FileDownload[]): string {
    const totalBytes = files.reduce((sum, file) => sum + file.size, 0);
    
    if (totalBytes < 1024) {
      return `${totalBytes} bytes`;
    } else if (totalBytes < 1024 * 1024) {
      return `${(totalBytes / 1024).toFixed(1)} KB`;
    } else {
      return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
    }
  }

  // Validate file content
  static validateFileContent(file: FileDownload): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    if (file.content.length === 0) {
      errors.push('File is empty');
    }
    
    if (file.type === 'sql') {
      // Basic SQL validation
      if (!file.content.trim().match(/^--|\bSELECT\b|\bCREATE\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b/i)) {
        errors.push('File does not appear to contain valid SQL');
      }
      
      // Check for potential issues
      if (file.content.includes('DROP DATABASE')) {
        errors.push('Contains potentially dangerous DROP DATABASE statement');
      }
    }
    
    if (file.type === 'json') {
      try {
        JSON.parse(file.content);
      } catch (e) {
        errors.push('Invalid JSON format');
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

// Export singleton instance
export const downloadSystem = new DownloadSystem();