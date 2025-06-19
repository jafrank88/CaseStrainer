<template>
  <div class="citation-network">
    <h2>Citation Network Visualization</h2>
    <p class="lead">This interactive visualization shows relationships between citations and their sources.</p>
    
    <div class="row mb-4">
      <div class="col-md-4">
        <div class="card">
          <div class="card-header">Visualization Controls</div>
          <div class="card-body">
            <div class="mb-3">
              <label for="networkType" class="form-label">Visualization Type:</label>
              <select class="form-select" id="networkType" v-model="visualizationType">
                <option value="force">Force-Directed Network</option>
                <option value="tree">Hierarchical Tree</option>
                <option value="cluster">Cluster View</option>
              </select>
            </div>
            <div class="mb-3">
              <label for="networkFilter" class="form-label">Filter By:</label>
              <select class="form-select" id="networkFilter" v-model="filter">
                <option value="all">All Citations</option>
                <option value="unconfirmed">Unconfirmed Citations Only</option>
                <option value="confirmed">Confirmed Citations Only</option>
              </select>
            </div>
            <div class="mb-3">
              <label for="networkDepth" class="form-label">Connection Depth:</label>
              <select class="form-select" id="networkDepth" v-model="depth">
                <option value="1">Direct Connections</option>
                <option value="2">Secondary Connections</option>
                <option value="3">Tertiary Connections</option>
              </select>
            </div>
            <button class="btn btn-primary" @click="generateNetwork">Generate Network</button>
          </div>
        </div>
      </div>
      <div class="col-md-8">
        <div class="card">
          <div class="card-header">Network Legend</div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-4">
                <div class="d-flex align-items-center mb-2">
                  <div class="me-2" style="width: 20px; height: 20px; background-color: #28a745; border-radius: 50%;"></div>
                  <span>Confirmed Citation</span>
                </div>
                <div class="d-flex align-items-center mb-2">
                  <div class="me-2" style="width: 20px; height: 20px; background-color: #ffc107; border-radius: 50%;"></div>
                  <span>Unconfirmed Citation</span>
                </div>
                <div class="d-flex align-items-center">
                  <div class="me-2" style="width: 20px; height: 20px; background-color: #dc3545; border-radius: 50%;"></div>
                  <span>Hallucinated Citation</span>
                </div>
              </div>
              <div class="col-md-4">
                <div class="d-flex align-items-center mb-2">
                  <div class="me-2" style="width: 20px; height: 20px; background-color: #007bff; border-radius: 50%;"></div>
                  <span>Source Document</span>
                </div>
                <div class="d-flex align-items-center mb-2">
                  <div class="me-2" style="width: 20px; height: 20px; background-color: #6c757d; border-radius: 50%;"></div>
                  <span>Referenced Case</span>
                </div>
                <div class="d-flex align-items-center">
                  <div class="me-2" style="width: 20px; height: 20px; background-color: #17a2b8; border-radius: 50%;"></div>
                  <span>Landmark Case</span>
                </div>
              </div>
              <div class="col-md-4">
                <div class="d-flex align-items-center mb-2">
                  <div class="me-2" style="width: 20px; height: 2px; background-color: #28a745;"></div>
                  <span>Strong Connection</span>
                </div>
                <div class="d-flex align-items-center mb-2">
                  <div class="me-2" style="width: 20px; height: 2px; background-color: #ffc107;"></div>
                  <span>Weak Connection</span>
                </div>
                <div class="d-flex align-items-center">
                  <div class="me-2" style="width: 20px; height: 2px; background-color: #dc3545; border-style: dashed;"></div>
                  <span>Questionable Connection</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="card">
      <div class="card-header">Citation Network</div>
      <div class="card-body">
        <div v-if="loading" class="text-center p-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2">Generating network visualization...</p>
        </div>
        <div v-else-if="error" class="alert alert-danger">
          {{ error }}
        </div>
        <div v-else-if="!networkData" class="text-center p-5">
          <p class="text-muted">Select your visualization options and click "Generate Network" to create a visualization.</p>
        </div>
        <div v-else>
          <div id="network-container" style="width: 100%; height: 600px; border: 1px solid #ddd;"></div>
          <div class="mt-3">
            <p><strong>Network Statistics:</strong></p>
            <div class="row">
              <div class="col-md-3">
                <div class="card text-center">
                  <div class="card-body">
                    <h5 class="card-title">{{ networkStats.nodes }}</h5>
                    <p class="card-text">Total Nodes</p>
                  </div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="card text-center">
                  <div class="card-body">
                    <h5 class="card-title">{{ networkStats.edges }}</h5>
                    <p class="card-text">Total Connections</p>
                  </div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="card text-center">
                  <div class="card-body">
                    <h5 class="card-title">{{ networkStats.confirmedNodes }}</h5>
                    <p class="card-text">Confirmed Citations</p>
                  </div>
                </div>
              </div>
              <div class="col-md-3">
                <div class="card text-center">
                  <div class="card-body">
                    <h5 class="card-title">{{ networkStats.unconfirmedNodes }}</h5>
                    <p class="card-text">Unconfirmed Citations</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as d3 from 'd3';
import api from '@/api/citations';

export default {
  name: 'CitationNetwork',
  data() {
    return {
      visualizationType: 'force',
      filter: 'all',
      depth: '1',
      loading: false,
      error: null,
      networkData: null,
      networkStats: {
        nodes: 0,
        edges: 0,
        confirmedNodes: 0,
        unconfirmedNodes: 0
      }
    };
  },
  methods: {
    async generateNetwork() {
      this.loading = true;
      this.error = null;
      
      try {
        // Fetch network data from API
        const response = await api.getCitationNetworkData(this.filter, this.depth);
        this.networkData = this.processDataForVisualization(response.data);
        
        // Calculate network statistics
        this.calculateNetworkStats();
        
        // Clear previous visualization
        d3.select('#network-container').html('');
        
        // Create visualization based on selected type
        switch (this.visualizationType) {
          case 'force':
            this.createForceDirectedGraph();
            break;
          case 'tree':
            this.createHierarchicalTree();
            break;
          case 'cluster':
            this.createClusterView();
            break;
          default:
            this.createForceDirectedGraph();
        }
      } catch (error) {
        console.error('Error generating network:', error);
        this.error = 'Failed to generate network visualization. Please try again.';
      } finally {
        this.loading = false;
      }
    },
    
    processDataForVisualization(data) {
      // Process the API response data into a format suitable for D3 visualization
      // This is a placeholder implementation - actual implementation would depend on API response format
      return {
        nodes: data.nodes || [],
        links: data.links || []
      };
    },
    
    calculateNetworkStats() {
      if (!this.networkData) return;
      
      const confirmedNodes = this.networkData.nodes.filter(node => node.status === 'confirmed').length;
      const unconfirmedNodes = this.networkData.nodes.filter(node => node.status === 'unconfirmed').length;
      
      this.networkStats = {
        nodes: this.networkData.nodes.length,
        edges: this.networkData.links.length,
        confirmedNodes,
        unconfirmedNodes
      };
    },
    
    createForceDirectedGraph() {
      if (!this.networkData) return;
      
      const container = document.getElementById('network-container');
      const width = container.clientWidth;
      const height = container.clientHeight;
      
      // Create SVG element
      const svg = d3.select('#network-container')
        .append('svg')
        .attr('width', width)
        .attr('height', height);
      
      // Define node colors based on status
      const nodeColor = d => {
        switch (d.type) {
          case 'source_document': return '#007bff'; // Source document - blue
          case 'referenced_case': return '#6c757d'; // Referenced case - gray
          case 'landmark_case': return '#17a2b8'; // Landmark case - teal
          default:
            switch (d.status) {
              case 'confirmed': return '#28a745'; // Confirmed - green
              case 'unconfirmed': return '#ffc107'; // Unconfirmed - yellow
              case 'hallucinated': return '#dc3545'; // Hallucinated - red
              default: return '#6c757d'; // Default - gray
            }
        }
      };
      
      // Define link colors based on strength
      const linkColor = d => {
        switch (d.strength) {
          case 'strong': return '#28a745'; // Strong - green
          case 'weak': return '#ffc107'; // Weak - yellow
          case 'questionable': return '#dc3545'; // Questionable - red
          default: return '#6c757d'; // Default - gray
        }
      };
      
      // Define link stroke style
      const linkStroke = d => {
        return d.strength === 'questionable' ? '3, 3' : '0';
      };
      
      // Create simulation
      const simulation = d3.forceSimulation(this.networkData.nodes)
        .force('link', d3.forceLink(this.networkData.links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));
      
      // Create links
      const link = svg.append('g')
        .selectAll('line')
        .data(this.networkData.links)
        .enter()
        .append('line')
        .attr('stroke', linkColor)
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', linkStroke);
      
      // Create nodes
      const node = svg.append('g')
        .selectAll('circle')
        .data(this.networkData.nodes)
        .enter()
        .append('circle')
        .attr('r', 10)
        .attr('fill', nodeColor)
        .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended));
      
      // Add node labels
      const label = svg.append('g')
        .selectAll('text')
        .data(this.networkData.nodes)
        .enter()
        .append('text')
        .text(d => d.name || d.id)
        .attr('font-size', 10)
        .attr('dx', 12)
        .attr('dy', 4);
      
      // Add tooltips
      node.append('title')
        .text(d => `${d.name || d.id}\nType: ${d.type}\nStatus: ${d.status}`);
      
      // Update positions on simulation tick
      simulation.on('tick', () => {
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);
        
        node
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);
        
        label
          .attr('x', d => d.x)
          .attr('y', d => d.y);
      });
      
      // Drag functions
      function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }
      
      function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
      }
      
      function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }
    },
    
    createHierarchicalTree() {
      // Implementation of hierarchical tree visualization
      // This is a placeholder - actual implementation would use D3 tree layout
      const container = document.getElementById('network-container');
      
      d3.select('#network-container')
        .append('div')
        .attr('class', 'alert alert-info')
        .text('Hierarchical Tree visualization is under development. Please try Force-Directed Network instead.');
    },
    
    createClusterView() {
      // Implementation of cluster view visualization
      // This is a placeholder - actual implementation would use D3 cluster layout
      const container = document.getElementById('network-container');
      
      d3.select('#network-container')
        .append('div')
        .attr('class', 'alert alert-info')
        .text('Cluster View visualization is under development. Please try Force-Directed Network instead.');
    }
  }
}
</script>
