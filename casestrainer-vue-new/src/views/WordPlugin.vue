<template>
  <div class="container py-5">
    <div class="row justify-content-center">
      <div class="col-lg-8 text-center">
        <h1 class="display-4 mb-3"><i class="bi bi-file-earmark-word me-2"></i> CaseStrainer Word Plug-in</h1>
        <p class="lead mb-4">Validate legal citations directly inside your Microsoft Word documents. Highlight, verify, and correct citations as you write.</p>
        <div class="alert alert-info py-4">
          <h4 class="mb-2">Coming Soon!</h4>
          <p>We are developing a Microsoft Word add-in for seamless in-document citation validation. Stay tuned for updates and download links.</p>
        </div>
        <router-link to="/" class="btn btn-primary mt-3">
          <i class="bi bi-house-door me-1"></i> Back to Home
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WordPlugin'
}
</script>

<style scoped>
.display-4 {
  font-weight: 700;
}
</style> 