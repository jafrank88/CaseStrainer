const uploadFile = async () => {
  if (!selectedFile.value) {
    errorMessage.value = "Please select a file first";
    return;
  }

  try {
    isUploading.value = true;
    errorMessage.value = null;
    uploadProgress.value = 0;

    // Create form data
    const formData = new FormData();
    formData.append("file", selectedFile.value);

    // Add file metadata
    const fileOptions = {
      convert_pdf_to_md: true,
      is_binary: true,
      file_type: selectedFile.value.type,
      file_ext: selectedFile.value.name.split('.').pop().toLowerCase()
    };
    formData.append("options", JSON.stringify(fileOptions));

    // Show upload progress
    const uploadStartTime = Date.now();
    const updateProgress = () => {
      const elapsed = Date.now() - uploadStartTime;
      if (elapsed < 30000) { // Only update progress for first 30 seconds
        uploadProgress.value = Math.min(95, Math.floor((elapsed / 30000) * 100));
        if (uploadProgress.value < 95) {
          setTimeout(updateProgress, 100);
        }
      }
    };
    updateProgress();

    // Make API request with timeout
    const response = await axios.post("/analyze", formData, {
      headers: {
        "Content-Type": "multipart/form-data"
      },
      timeout: 30000, // 30 second timeout
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          uploadProgress.value = Math.min(95, Math.floor((progressEvent.loaded / progressEvent.total) * 100));
        }
      }
    });

    // Handle successful response
    uploadProgress.value = 100;
    const result = response.data;

    // Check for errors in response
    if (result.error) {
      throw new Error(result.error);
    }

    // Emit success event
    emit("upload-success", result);

  } catch (error) {
    console.error("File upload error:", error);
    
    // Handle specific error cases
    if (error.code === 'ECONNABORTED') {
      errorMessage.value = "The upload took too long. Please try a smaller file or check your connection.";
    } else if (error.response) {
      // Server responded with an error
      const serverError = error.response.data.error || error.response.data.message;
      errorMessage.value = serverError || "Server error occurred. Please try again.";
    } else if (error.request) {
      // No response received
      errorMessage.value = "No response from server. Please check your connection and try again.";
    } else {
      // Other errors
      errorMessage.value = error.message || "An error occurred during upload. Please try again.";
    }
    
    emit("upload-error", {
      message: errorMessage.value,
      details: error.response?.data || null,
      status: error.response?.status || 500
    });
  } finally {
    isUploading.value = false;
    if (errorMessage.value) {
      uploadProgress.value = 0;
    }
  }
}; 