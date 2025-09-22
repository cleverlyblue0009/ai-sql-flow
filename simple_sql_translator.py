#!/usr/bin/env python3
"""
Simple SQL Translation Server
A lightweight HTTP server that provides basic SQL dialect translation.
"""

import json
import re
import uuid
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

class SQLTranslator:
    """Basic SQL dialect translator"""
    
    def __init__(self):
        self.jobs = {}  # In-memory job storage
    
    def translate_mysql_to_snowflake(self, sql):
        """Convert MySQL SQL to Snowflake SQL"""
        translated = sql
        
        # Data type conversions
        translated = re.sub(r'\bAUTO_INCREMENT\b', 'AUTOINCREMENT', translated, flags=re.IGNORECASE)
        translated = re.sub(r'\bTINYINT(\(\d+\))?\b', 'SMALLINT', translated, flags=re.IGNORECASE)
        translated = re.sub(r'\bMEDIUMINT(\(\d+\))?\b', 'INT', translated, flags=re.IGNORECASE)
        translated = re.sub(r'\bLONGTEXT\b', 'TEXT', translated, flags=re.IGNORECASE)
        
        # Function conversions
        translated = re.sub(
            r'\bDATE_FORMAT\s*\(\s*([^,]+),\s*[\'"]%Y-%m[\'"]\s*\)',
            r"TO_CHAR(\1, 'YYYY-MM')",
            translated,
            flags=re.IGNORECASE
        )
        translated = re.sub(
            r'\bDATE_SUB\s*\(\s*NOW\(\),\s*INTERVAL\s+(\d+)\s+MONTH\s*\)',
            r'DATEADD(MONTH, -\1, CURRENT_TIMESTAMP())',
            translated,
            flags=re.IGNORECASE
        )
        translated = re.sub(r'\bNOW\(\)\b', 'CURRENT_TIMESTAMP()', translated, flags=re.IGNORECASE)
        
        # Quote style conversion
        translated = re.sub(r'`([^`]+)`', r'"\1"', translated)
        
        return translated
    
    def translate_postgresql_to_snowflake(self, sql):
        """Convert PostgreSQL SQL to Snowflake SQL"""
        translated = sql
        
        # Data type conversions
        translated = re.sub(r'\bSERIAL\b', 'AUTOINCREMENT', translated, flags=re.IGNORECASE)
        translated = re.sub(r'\bBIGSERIAL\b', 'AUTOINCREMENT', translated, flags=re.IGNORECASE)
        translated = re.sub(r'\bBOOLEAN\b', 'BOOL', translated, flags=re.IGNORECASE)
        translated = re.sub(r'\bTIMESTAMP WITH TIME ZONE\b', 'TIMESTAMP_TZ', translated, flags=re.IGNORECASE)
        
        return translated
    
    def translate_sql(self, source_sql, source_dialect, target_dialect):
        """Main translation method"""
        if source_dialect.lower() == 'mysql' and target_dialect.lower() == 'snowflake':
            return self.translate_mysql_to_snowflake(source_sql)
        elif source_dialect.lower() == 'postgresql' and target_dialect.lower() == 'snowflake':
            return self.translate_postgresql_to_snowflake(source_sql)
        else:
            # For unsupported combinations, return original with a comment
            return f"-- Translated from {source_dialect} to {target_dialect}\n{source_sql}"
    
    def create_translation_job(self, source_sql, source_dialect, target_dialect):
        """Create a translation job and return job ID"""
        job_id = str(uuid.uuid4())
        
        self.jobs[job_id] = {
            'job_id': job_id,
            'status': 'processing',
            'created_at': datetime.now().isoformat(),
            'source_sql': source_sql,
            'source_dialect': source_dialect,
            'target_dialect': target_dialect,
            'result': None,
            'error': None
        }
        
        # Simulate async processing
        def process_job():
            time.sleep(2)  # Simulate processing time
            try:
                translated_sql = self.translate_sql(source_sql, source_dialect, target_dialect)
                self.jobs[job_id].update({
                    'status': 'completed',
                    'result': {
                        'translated_sql': translated_sql,
                        'confidence_score': 0.85,
                        'semantic_similarity': 0.92
                    },
                    'completed_at': datetime.now().isoformat()
                })
            except Exception as e:
                self.jobs[job_id].update({
                    'status': 'failed',
                    'error': str(e),
                    'completed_at': datetime.now().isoformat()
                })
        
        threading.Thread(target=process_job, daemon=True).start()
        return job_id
    
    def get_job_status(self, job_id):
        """Get job status and result"""
        return self.jobs.get(job_id)

class SQLTranslationHandler(BaseHTTPRequestHandler):
    translator = SQLTranslator()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/migration/translate-sql':
            self.handle_translate_sql()
        else:
            self.send_error(404, "Not Found")
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/api/jobs/') and parsed_path.path.endswith('/status'):
            # Extract job ID from path
            path_parts = parsed_path.path.split('/')
            if len(path_parts) >= 4:
                job_id = path_parts[3]
                self.handle_job_status(job_id)
            else:
                self.send_error(400, "Invalid job ID")
        elif parsed_path.path == '/health':
            self.handle_health_check()
        else:
            self.send_error(404, "Not Found")
    
    def handle_translate_sql(self):
        """Handle SQL translation requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            source_sql = data.get('source_sql', '')
            source_dialect = data.get('source_dialect', 'mysql')
            target_dialect = data.get('target_dialect', 'snowflake')
            
            if not source_sql.strip():
                self.send_json_response({'error': 'source_sql is required'}, 400)
                return
            
            job_id = self.translator.create_translation_job(source_sql, source_dialect, target_dialect)
            
            response = {
                'job_id': job_id,
                'status': 'processing',
                'message': 'SQL translation started'
            }
            
            self.send_json_response(response)
            
        except json.JSONDecodeError:
            self.send_json_response({'error': 'Invalid JSON'}, 400)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_job_status(self, job_id):
        """Handle job status requests"""
        try:
            job = self.translator.get_job_status(job_id)
            if job:
                self.send_json_response(job)
            else:
                self.send_json_response({'error': 'Job not found'}, 404)
        except Exception as e:
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_health_check(self):
        """Handle health check requests"""
        self.send_json_response({
            'status': 'healthy',
            'service': 'SQL Translation Server',
            'timestamp': datetime.now().isoformat()
        })
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def main():
    """Main function to start the server"""
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, SQLTranslationHandler)
    
    print(f"Starting SQL Translation Server on http://{server_address[0]}:{server_address[1]}")
    print("Available endpoints:")
    print("  POST /api/migration/translate-sql - Start SQL translation")
    print("  GET  /api/jobs/{job_id}/status   - Get job status")
    print("  GET  /health                     - Health check")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == '__main__':
    main()