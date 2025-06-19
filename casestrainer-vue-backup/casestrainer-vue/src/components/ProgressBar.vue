<template>
  <div v-if="loading" class="mb-3">
    <div class="progress">
      <div class="progress-bar progress-bar-striped progress-bar-animated bg-info" role="progressbar" style="width: 100%">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProgressBar',
  props: {
    loading: {
      type: Boolean,
      required: true
    },
    message: {
      type: String,
      default: 'Loading...'
    }
  }
};
</script>

<style scoped>
.progress-bar {
  font-weight: 500;
  font-size: 1rem;
}
</style>
