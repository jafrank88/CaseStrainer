def _handle_file_upload():
    """Handle file upload with proper async RQ worker processing"""
    try:
        # Get Redis connection for async processing
        from rq import Queue
        from redis import Redis
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided', 'citations': [], 'clusters': []}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected', 'citations': [], 'clusters': []}), 400
        
        # Validate file type
        allowed_extensions = {'pdf', 'txt', 'doc', 'docx', 'rtf'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}', 'citations': [], 'clusters': []}), 400
        
        # Generate unique filename
        filename = file.filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Ensure uploads directory exists
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save file temporarily
        temp_file_path = os.path.join(uploads_dir, unique_filename)
        file.save(temp_file_path)
        
        try:
            # Generate task ID for async processing
            task_id = str(uuid.uuid4())
            
            # Get Redis connection with production defaults and better error handling
            redis_url = os.environ.get('REDIS_URL', 'redis://:***REDACTED_REDIS_PASSWORD***@redis:6379/0')
            logger.info(f"Connecting to Redis at: {redis_url}")
            
            try:
                redis_conn = Redis.from_url(redis_url, socket_connect_timeout=5, socket_timeout=5)
                # Test the connection
                if not redis_conn.ping():
                    raise Exception("Redis ping failed")
                queue = Queue('casestrainer', connection=redis_conn)
                logger.info("Successfully connected to Redis")
            except Exception as e:
                logger.error(f"Redis connection error: {e}", exc_info=True)
                raise Exception(f"Failed to connect to Redis: {str(e)}")
            
            # Queue the task for background processing
            job = queue.enqueue(
                citation_service.process_citation_task,
                task_id,
                'file',
                {
                    'file_path': temp_file_path,
                    'filename': filename,
                    'file_ext': file_ext
                },
                job_id=task_id,
                job_timeout='10m',
                result_ttl=3600  # Keep results for 1 hour
            )
            
            logger.info(f"Queued file processing task {task_id} for background processing")
            
            # Return immediately with task ID for polling
            return jsonify({
                'status': 'processing',
                'task_id': task_id,
                'message': 'File uploaded and queued for processing',
                'job_id': job.id,
                'success': True
            }), 202  # 202 Accepted
            
        except Exception as e:
            # Ensure cleanup even if queuing fails
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            logger.error(f"Error queuing file processing task: {e}", exc_info=True)
            raise
            
    except Exception as e:
        logger.error(f"File upload error: {e}", exc_info=True)
        return jsonify({'error': f'Failed to process file: {str(e)}', 'citations': [], 'clusters': []}), 500
