import { useState, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster, toast } from "sonner";
import axios from "axios";
import { 
  Camera, 
  ScanLine, 
  Zap, 
  AlertTriangle, 
  CheckCircle, 
  Menu, 
  X, 
  Upload,
  ArrowLeft,
  Info,
  Flame,
  Droplets,
  Cookie,
  Wheat,
  Dna,
  Sparkles
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle 
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Navbar Component
const Navbar = ({ onMenuClick, isMenuOpen }) => {
  return (
    <nav 
      className="fixed top-0 w-full z-50 glass border-b border-white/5 h-16"
      data-testid="navbar"
    >
      <div className="max-w-6xl mx-auto h-full flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-green-600 flex items-center justify-center neon-glow">
            <ScanLine className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-xl tracking-tight font-['Manrope']">
            <span className="gradient-text">Nutri</span>
            <span className="text-zinc-50">Scan</span>
          </span>
        </div>
        
        <button 
          onClick={onMenuClick}
          className="p-2 rounded-lg hover:bg-zinc-800/50 transition-colors duration-200"
          data-testid="menu-toggle"
          aria-label="Toggle menu"
        >
          {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>
    </nav>
  );
};

// Footer Component
const Footer = () => {
  return (
    <footer 
      className="bg-black border-t border-zinc-900 py-12 px-6"
      data-testid="footer"
    >
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col items-center gap-8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-green-600/20 flex items-center justify-center">
              <ScanLine className="w-4 h-4 text-green-500" />
            </div>
            <span className="font-semibold text-zinc-400">NutriScan AI</span>
          </div>
          
          <div className="flex flex-wrap justify-center gap-6 text-sm">
            <a 
              href="/privacy" 
              className="text-zinc-500 hover:text-zinc-300 transition-colors duration-200"
              data-testid="footer-privacy-link"
            >
              Política de Privacidad
            </a>
            <a 
              href="/terms" 
              className="text-zinc-500 hover:text-zinc-300 transition-colors duration-200"
              data-testid="footer-terms-link"
            >
              Términos de Uso
            </a>
            <a 
              href="/contact" 
              className="text-zinc-500 hover:text-zinc-300 transition-colors duration-200"
              data-testid="footer-contact-link"
            >
              Contacto
            </a>
          </div>
          
          <p className="text-xs text-zinc-600 text-center max-w-md">
            © {new Date().getFullYear()} NutriScan AI. Todos los derechos reservados. 
            La información nutricional es orientativa y no sustituye el consejo médico profesional.
          </p>
        </div>
      </div>
    </footer>
  );
};

// Scan Button Component
const ScanButton = ({ onClick }) => {
  return (
    <button
      onClick={onClick}
      className="scan-button h-32 w-32 rounded-full bg-green-600 text-white flex items-center justify-center animate-pulse-glow neon-glow-strong transition-transform duration-300 hover:scale-105 active:scale-95"
      data-testid="scan-button"
      aria-label="Escanear etiqueta"
    >
      <Camera className="w-12 h-12" />
    </button>
  );
};

// Camera Modal Component
const CameraModal = ({ isOpen, onClose, onCapture, isLoading }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleCapture = () => {
    if (selectedFile) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result?.toString().split(',')[1];
        onCapture(base64);
      };
      reader.readAsDataURL(selectedFile);
    } else {
      // Simulate capture without file
      onCapture(null);
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="bg-zinc-950 border-zinc-800 max-w-md mx-auto p-0 overflow-hidden">
        <DialogHeader className="p-6 pb-0">
          <DialogTitle className="text-xl font-semibold text-zinc-50 flex items-center gap-2">
            <Camera className="w-5 h-5 text-green-500" />
            Escanear Etiqueta
          </DialogTitle>
        </DialogHeader>
        
        <div className="p-6 flex flex-col items-center gap-6">
          {/* Viewfinder */}
          <div className="viewfinder relative bg-zinc-900/50 flex items-center justify-center overflow-hidden">
            <div className="viewfinder-corner-tr" />
            <div className="viewfinder-corner-bl" />
            
            {previewUrl ? (
              <img 
                src={previewUrl} 
                alt="Preview" 
                className="w-full h-full object-cover"
                data-testid="image-preview"
              />
            ) : (
              <div className="text-center p-4">
                <Upload className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                <p className="text-sm text-zinc-500">
                  Sube una foto de la etiqueta nutricional
                </p>
              </div>
            )}
            
            {/* Scan line animation */}
            {isLoading && (
              <div className="scan-line animate-scan-line" />
            )}
          </div>

          {/* Actions */}
          <div className="w-full flex flex-col gap-3">
            {!isLoading && (
              <>
                <label className="file-input-wrapper">
                  <Button 
                    variant="outline" 
                    className="w-full border-zinc-700 bg-zinc-900/50 hover:bg-zinc-800 text-zinc-300"
                    data-testid="upload-button"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    {selectedFile ? 'Cambiar imagen' : 'Subir imagen'}
                  </Button>
                  <input 
                    type="file" 
                    accept="image/*" 
                    onChange={handleFileSelect}
                    data-testid="file-input"
                  />
                </label>

                <Button 
                  onClick={handleCapture}
                  className="w-full bg-green-600 hover:bg-green-500 text-white neon-glow"
                  data-testid="analyze-button"
                >
                  <ScanLine className="w-4 h-4 mr-2" />
                  {selectedFile ? 'Analizar imagen' : 'Usar ejemplo'}
                </Button>
              </>
            )}

            {isLoading && (
              <div className="text-center py-4">
                <div className="loading-spinner animate-spin-slow mx-auto mb-4" />
                <p className="text-sm text-zinc-400 animate-pulse">
                  Analizando etiqueta nutricional...
                </p>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Nutrient Card Component
const NutrientCard = ({ nutrient, index }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'good': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'danger': return 'text-red-500';
      default: return 'text-zinc-400';
    }
  };

  const getBarColor = (status) => {
    switch (status) {
      case 'good': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'danger': return 'bg-red-500';
      default: return 'bg-zinc-500';
    }
  };

  const getIcon = (name) => {
    const iconMap = {
      'Calorías': Flame,
      'Grasas': Droplets,
      'Carbohidratos': Cookie,
      'Fibra': Wheat,
      'Proteínas': Dna,
    };
    const key = Object.keys(iconMap).find(k => name.toLowerCase().includes(k.toLowerCase()));
    return key ? iconMap[key] : Sparkles;
  };

  const Icon = getIcon(nutrient.name);

  return (
    <div 
      className={`glass-light p-4 rounded-2xl opacity-0 animate-fade-in-up stagger-${index + 1}`}
      data-testid={`nutrient-card-${nutrient.name.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center ${getStatusColor(nutrient.status)}`}>
            <Icon className="w-4 h-4" />
          </div>
          <span className="text-sm text-zinc-400">{nutrient.name}</span>
        </div>
        {nutrient.percentage && (
          <span className="text-xs text-zinc-500">{nutrient.percentage}% VD</span>
        )}
      </div>
      
      <div className="flex items-end justify-between mb-2">
        <span className={`text-2xl font-bold ${getStatusColor(nutrient.status)}`}>
          {nutrient.value}
        </span>
        <span className="text-sm text-zinc-500">{nutrient.unit}</span>
      </div>
      
      {nutrient.percentage && (
        <div className="nutrient-bar">
          <div 
            className={`nutrient-bar-fill ${getBarColor(nutrient.status)}`}
            style={{ width: `${Math.min(nutrient.percentage * 2, 100)}%` }}
          />
        </div>
      )}
    </div>
  );
};

// Health Score Component
const HealthScore = ({ score }) => {
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (score / 100) * circumference;
  
  const getScoreColor = (score) => {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#eab308';
    return '#ef4444';
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Excelente';
    if (score >= 60) return 'Bueno';
    if (score >= 40) return 'Regular';
    return 'Mejorable';
  };

  return (
    <div className="health-score-circle flex items-center justify-center" data-testid="health-score">
      <svg className="progress-ring w-full h-full" viewBox="0 0 100 100">
        <circle
          className="health-score-bg"
          cx="50"
          cy="50"
          r="45"
        />
        <circle
          className="health-score-fill"
          cx="50"
          cy="50"
          r="45"
          stroke={getScoreColor(score)}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
        />
      </svg>
      <div className="absolute text-center">
        <span className="text-3xl font-bold" style={{ color: getScoreColor(score) }}>
          {score}
        </span>
        <p className="text-xs text-zinc-500 mt-1">{getScoreLabel(score)}</p>
      </div>
    </div>
  );
};

// Results View Component
const ResultsView = ({ result, onBack }) => {
  if (!result) return null;

  return (
    <div className="min-h-screen bg-zinc-950 pt-20 pb-8 px-4" data-testid="results-view">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8 opacity-0 animate-fade-in-up">
          <button 
            onClick={onBack}
            className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 transition-colors duration-200"
            data-testid="back-button"
            aria-label="Volver"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-zinc-50 font-['Manrope']">
              Resultado del Análisis
            </h1>
            <p className="text-sm text-zinc-500">
              {new Date(result.timestamp).toLocaleString('es-ES')}
            </p>
          </div>
        </div>

        {/* Product Info */}
        <Card className="bg-zinc-900/50 border-zinc-800 mb-6 opacity-0 animate-fade-in-up stagger-1">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="w-20 h-20 rounded-xl bg-zinc-800 flex items-center justify-center overflow-hidden">
                <img 
                  src="https://images.unsplash.com/photo-1702724122866-8898b15ebeac?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NjZ8MHwxfHNlYXJjaHwxfHxmb29kJTIwcHJvZHVjdCUyMHBhY2thZ2luZyUyMGJvdHRsZSUyMGphcnxlbnwwfHx8fDE3NzI1NDkyOTl8MA&ixlib=rb-4.1.0&q=85"
                  alt={result.product_name}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-zinc-50" data-testid="product-name">
                  {result.product_name}
                </h2>
                <p className="text-sm text-zinc-500" data-testid="product-brand">
                  {result.brand}
                </p>
                <Badge variant="outline" className="mt-2 text-xs border-zinc-700 text-zinc-400">
                  {result.serving_size}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Health Score */}
        <div className="glass rounded-2xl p-6 mb-6 flex flex-col items-center opacity-0 animate-fade-in-up stagger-2">
          <h3 className="text-sm font-medium text-zinc-400 mb-4">Puntuación de Salud</h3>
          <HealthScore score={result.health_score} />
        </div>

        {/* Nutrients Grid */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-zinc-400 mb-4 px-1">
            Información Nutricional
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {result.nutrients.map((nutrient, index) => (
              <NutrientCard key={nutrient.name} nutrient={nutrient} index={index} />
            ))}
          </div>
        </div>

        {/* Warnings */}
        {result.warnings.length > 0 && (
          <Card className="bg-yellow-500/5 border-yellow-500/20 mb-6 opacity-0 animate-fade-in-up stagger-6">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-yellow-500" />
                <h3 className="text-sm font-medium text-yellow-500">Advertencias</h3>
              </div>
              <ul className="space-y-2">
                {result.warnings.map((warning, index) => (
                  <li 
                    key={index} 
                    className="text-sm text-zinc-400 flex items-start gap-2"
                    data-testid={`warning-${index}`}
                  >
                    <span className="text-yellow-500 mt-1">•</span>
                    {warning}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Recommendations */}
        {result.recommendations.length > 0 && (
          <Card className="bg-green-500/5 border-green-500/20 opacity-0 animate-fade-in-up stagger-7">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <h3 className="text-sm font-medium text-green-500">Recomendaciones</h3>
              </div>
              <ul className="space-y-2">
                {result.recommendations.map((rec, index) => (
                  <li 
                    key={index} 
                    className="text-sm text-zinc-400 flex items-start gap-2"
                    data-testid={`recommendation-${index}`}
                  >
                    <span className="text-green-500 mt-1">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* New Scan Button */}
        <div className="mt-8 flex justify-center">
          <Button 
            onClick={onBack}
            className="bg-green-600 hover:bg-green-500 text-white px-8 neon-glow"
            data-testid="new-scan-button"
          >
            <Camera className="w-4 h-4 mr-2" />
            Nuevo Escaneo
          </Button>
        </div>
      </div>
    </div>
  );
};

// Home Page Component
const Home = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleScan = useCallback(() => {
    setIsCameraOpen(true);
  }, []);

  const handleCapture = async (imageBase64) => {
    setIsLoading(true);
    
    try {
      const response = await axios.post(`${API}/analyze`, {
        image_base64: imageBase64
      });
      
      setAnalysisResult(response.data);
      setIsCameraOpen(false);
      toast.success('¡Análisis completado!', {
        description: 'Se ha analizado la etiqueta correctamente.'
      });
    } catch (error) {
      console.error('Error analyzing label:', error);
      toast.error('Error al analizar', {
        description: 'No se pudo completar el análisis. Intenta de nuevo.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = useCallback(() => {
    setAnalysisResult(null);
  }, []);

  // If we have results, show results view
  if (analysisResult) {
    return (
      <>
        <Navbar onMenuClick={() => setIsMenuOpen(!isMenuOpen)} isMenuOpen={isMenuOpen} />
        <ResultsView result={analysisResult} onBack={handleBack} />
        <Footer />
      </>
    );
  }

  return (
    <>
      <Navbar onMenuClick={() => setIsMenuOpen(!isMenuOpen)} isMenuOpen={isMenuOpen} />
      
      {/* Hero Section */}
      <main className="hero-bg min-h-screen flex flex-col" data-testid="home-page">
        <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 pt-24 pb-16">
          {/* Main Content */}
          <div className="text-center max-w-lg mx-auto mb-12 opacity-0 animate-fade-in-up">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6 font-['Manrope']">
              <span className="gradient-text">Escanea</span>
              <br />
              <span className="text-zinc-50">tu alimentación</span>
            </h1>
            <p className="text-base text-zinc-400 leading-relaxed max-w-md mx-auto">
              Analiza las etiquetas nutricionales de tus productos y toma decisiones más saludables con inteligencia artificial.
            </p>
          </div>

          {/* Scan Button */}
          <div className="mb-8 opacity-0 animate-fade-in-up stagger-2">
            <ScanButton onClick={handleScan} />
          </div>

          {/* CTA Text */}
          <p className="text-sm text-zinc-500 animate-bounce-subtle opacity-0 animate-fade-in stagger-3">
            Toca para escanear una etiqueta
          </p>

          {/* Features */}
          <div className="grid grid-cols-3 gap-4 mt-16 max-w-md w-full opacity-0 animate-fade-in-up stagger-4">
            <div className="text-center">
              <div className="w-12 h-12 rounded-xl bg-zinc-900/80 border border-zinc-800 flex items-center justify-center mx-auto mb-2">
                <Zap className="w-5 h-5 text-green-500" />
              </div>
              <p className="text-xs text-zinc-500">Análisis<br/>Instantáneo</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 rounded-xl bg-zinc-900/80 border border-zinc-800 flex items-center justify-center mx-auto mb-2">
                <Info className="w-5 h-5 text-green-500" />
              </div>
              <p className="text-xs text-zinc-500">Info<br/>Detallada</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 rounded-xl bg-zinc-900/80 border border-zinc-800 flex items-center justify-center mx-auto mb-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
              </div>
              <p className="text-xs text-zinc-500">Recomendaciones<br/>Personalizadas</p>
            </div>
          </div>
        </div>
      </main>

      <Footer />

      {/* Camera Modal */}
      <CameraModal 
        isOpen={isCameraOpen} 
        onClose={() => setIsCameraOpen(false)}
        onCapture={handleCapture}
        isLoading={isLoading}
      />

      {/* Toast notifications */}
      <Toaster 
        position="top-center" 
        richColors 
        toastOptions={{
          style: {
            background: '#18181b',
            border: '1px solid #27272a',
            color: '#fafafa'
          }
        }}
      />
    </>
  );
};

function App() {
  return (
    <div className="min-h-screen bg-zinc-950">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/privacy" element={<Home />} />
          <Route path="/terms" element={<Home />} />
          <Route path="/contact" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
