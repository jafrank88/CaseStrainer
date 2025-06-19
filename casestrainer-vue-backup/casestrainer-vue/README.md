# CaseStrainer Vue.js Frontend

This is the modern Vue.js frontend for the CaseStrainer application, designed to replace the original AJAX-based implementation with a more maintainable and feature-rich single-page application.

## Features

- **Modern Component-Based Architecture**: Built with Vue.js 3 and Vuex for state management
- **Responsive Design**: Uses Bootstrap 5 for responsive layouts that work on all devices
- **Interactive Visualizations**: D3.js integration for citation network visualization
- **Improved User Experience**: Smoother transitions, better feedback, and more intuitive interface
- **Modular Structure**: Organized into reusable components for easier maintenance and extension

## Project Structure

```
casestrainer-vue/
├── public/              # Static assets
├── src/
│   ├── api/             # API service modules
│   ├── assets/          # Images, fonts, etc.
│   ├── components/      # Reusable Vue components
│   ├── router/          # Vue Router configuration
│   ├── store/           # Vuex store modules
│   │   └── modules/     # Feature-specific store modules
│   ├── views/           # Page components
│   ├── App.vue          # Root component
│   └── main.js          # Application entry point
├── package.json         # Dependencies and scripts
└── vue.config.js        # Vue CLI configuration
```

## Development Setup

### Prerequisites

- Node.js (v14+)
- npm or yarn

### Installation

1. Clone the repository
2. Navigate to the project directory:
   ```
   cd casestrainer-vue
   ```
3. Install dependencies:
   ```
   npm install
   ```
   or
   ```
   yarn install
   ```

### Running the Development Server

```
npm run serve
```
or
```
yarn serve
```

This will start the development server at http://localhost:8080. The Vue.js frontend will proxy API requests to the Flask backend running on port 5000.

### Building for Production

```
npm run build
```
or
```
yarn build
```

This will create a production-ready build in the `dist` directory.

## Deployment

The Vue.js frontend is configured to be deployed to the `/casestrainer/` path in production, which matches the Nginx proxy configuration. The built files should be placed in a directory that the Flask application can serve.

See `DEPLOYMENT.md` in the main project directory for detailed deployment instructions.

## Integration with Flask Backend

The Vue.js frontend communicates with the Flask backend through a RESTful API. The API endpoints are defined in the `src/api/citations.js` file.

In development mode, API requests are proxied to `http://localhost:5000` as configured in `vue.config.js`.

In production mode, the frontend expects the backend to be available at the same domain under the `/casestrainer/api` path.

## Features Implemented

- **Home**: Overview of the application with quick links to main features
- **Unconfirmed Citations**: Browse and filter the database of unconfirmed citations
- **Multitool Confirmed**: View citations confirmed with the multi-source verification tool
- **Citation Network**: Interactive visualization of citation relationships
- **ML Classifier**: Machine learning-based citation classification
- **Citation Tester**: Test the citation verification system with random citations
- **About**: Information about the application and its features

## Future Enhancements

See the roadmap in the About section of the application for planned future enhancements.
