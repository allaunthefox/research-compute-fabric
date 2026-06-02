<%*
// Template configuration for Research Stack
// This file configures the Templater plugin for various research workflows

// Helper function to generate unique IDs
function generateId() {
  return Math.random().toString(36).substr(2, 9);
}

// Helper function to get current date in various formats
function getDate(format = 'YYYY-MM-DD', offset = 0) {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  
  switch(format) {
    case 'YYYY-MM-DD':
      return `${year}-${month}-${day}`;
    case 'YYYY-MM-DDTHH:mm:ssZ':
      return `${year}-${month}-${day}T${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}Z`;
    default:
      return `${year}-${month}-${day}`;
  }
}

// Research stack specific helpers
const researchHelpers = {
  // Generate receipt hash
  generateReceiptHash: function() {
    return 'receipt_' + generateId();
  },
  
  // Get layer information
  getLayerInfo: function(layer) {
    const layers = {
      'L0': { name: 'Primordial', color: '#ff6b6b', description: 'Pure math, fixed-point arithmetic' },
      'L1': { name: 'Geometric', color: '#4ecdc4', description: 'Shape-aware topology' },
      'L2': { name: 'Biological', color: '#45b7d1', description: 'Genetic codes, spiking neurons' },
      'L3': { name: 'Thermodynamic', color: '#96ceb4', description: 'Energy-aware quality' },
      'L4': { name: 'Security', color: '#feca57', description: 'Attack-aware gating' },
      'L5': { name: 'Semantic', color: '#ff9ff3', description: 'Meaning-aware filtering' },
      'L6': { name: 'Meta', color: '#a29bfe', description: 'Self-aware adaptation' }
    };
    return layers[layer] || { name: 'Unknown', color: '#999999', description: 'Unknown layer' };
  },
  
  // Generate Lean code stub
  generateLeanStub: function(theoremName) {
    return `theorem ${theoremName} [hypotheses] : conclusion :=
  sorry`;
  },
  
  // Generate receipt stub
  generateReceiptStub: function(receiptName) {
    return `def ${receiptName}Receipt (state : State) : String :=
  "${receiptName}:" ++ toString state.val ++ ","`;
  }
};

// Make helpers available globally
tp.research = researchHelpers;
tp.utils = {
  generateId,
  getDate
};
*%>

<%*
// Main template logic based on file type
const templateType = tp.file.frontmatter?.type || 'note';

switch(templateType) {
  case 'formal-proof':
    // Add formal proof specific processing
    break;
  case 'attack-plan':
    // Add attack plan specific processing
    break;
  case 'receipt':
    // Add receipt specific processing
    break;
  case 'milestone':
    // Add milestone specific processing
    break;
  default:
    // Generic note processing
    break;
}
*%>