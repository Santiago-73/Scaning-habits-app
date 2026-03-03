import { useState, useCallback, useEffect, useRef, createContext, useContext } from "react";
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
  Upload,
  ArrowLeft,
  Info,
  Flame,
  Droplets,
  Cookie,
  Wheat,
  Dna,
  Sparkles,
  User,
  LogOut,
  Settings,
  Shield,
  AlertCircle,
  Heart,
  Scale,
  Ruler,
  UserCircle,
  Send,
  MessageCircle,
  Bot,
  Target,
  Activity
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogDescription
} from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ==================== AUTH CONTEXT ====================
const AuthContext = createContext(null);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('nutriscan_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const savedToken = localStorage.getItem('nutriscan_token');
      if (savedToken) {
        try {
          const response = await axios.get(`${API}/auth/me`, {
            headers: { Authorization: `Bearer ${savedToken}` }
          });
          setUser(response.data);
          setToken(savedToken);
        } catch (error) {
          localStorage.removeItem('nutriscan_token');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    localStorage.setItem('nutriscan_token', response.data.token);
    setToken(response.data.token);
    setUser(response.data.user);
    return response.data;
  };

  const register = async (name, email, password, profile) => {
    const response = await axios.post(`${API}/auth/register`, { 
      name, email, password, profile 
    });
    localStorage.setItem('nutriscan_token', response.data.token);
    setToken(response.data.token);
    setUser(response.data.user);
    return response.data;
  };

  const logout = async () => {
    try {
      if (token) {
        await axios.post(`${API}/auth/logout`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
    } catch (e) {
      console.error("Logout error:", e);
    }
    localStorage.removeItem('nutriscan_token');
    setToken(null);
    setUser(null);
  };

  const updateProfile = async (profileData) => {
    const response = await axios.put(`${API}/auth/profile`, profileData, {
      headers: { Authorization: `Bearer ${token}` }
    });
    setUser(response.data);
    return response.data;
  };

  const value = { user, token, loading, login, register, logout, updateProfile };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

// ==================== CONSTANTS ====================
const ALLERGY_OPTIONS = [
  { id: "gluten", label: "Gluten" },
  { id: "lactose", label: "Lactosa" },
  { id: "nuts", label: "Frutos secos" },
  { id: "eggs", label: "Huevo" },
  { id: "shellfish", label: "Mariscos" },
  { id: "soy", label: "Soja" },
  { id: "fish", label: "Pescado" },
];

const CONDITION_OPTIONS = [
  { id: "celiac", label: "Celiaco/a" },
  { id: "diabetic", label: "Diabético/a" },
  { id: "hypertensive", label: "Hipertenso/a" },
  { id: "cholesterol", label: "Colesterol alto" },
];

const ACTIVITY_OPTIONS = [
  { id: "sedentary", label: "Sedentario" },
  { id: "light", label: "Actividad ligera" },
  { id: "moderate", label: "Moderada" },
  { id: "active", label: "Activa" },
  { id: "very_active", label: "Muy activa" },
];

const GOAL_OPTIONS = [
  { id: "lose_weight", label: "Perder peso" },
  { id: "maintain", label: "Mantener peso" },
  { id: "gain_muscle", label: "Ganar músculo" },
  { id: "health", label: "Mejorar salud" },
];

const STRICTNESS_OPTIONS = [
  { id: "relaxed", label: "Relajado", desc: "Consejos suaves y comprensivos" },
  { id: "normal", label: "Normal", desc: "Información equilibrada" },
  { id: "strict", label: "Estricto", desc: "Críticas honestas y directas" },
  { id: "very_strict", label: "Sin filtros", desc: "La verdad cruda sobre la comida" },
];

// ==================== AUTH MODAL ====================
const AuthModal = ({ isOpen, onClose, onSuccess, initialMode = "login" }) => {
  const [mode, setMode] = useState(initialMode);
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    weight: "",
    height: "",
    sex: "",
    allergies: [],
    conditions: [],
    activity_level: "",
    goal: "",
    strictness_level: "normal"
  });

  const { login, register } = useAuth();

  const resetForm = () => {
    setFormData({
      name: "", email: "", password: "",
      weight: "", height: "", sex: "",
      allergies: [], conditions: [],
      activity_level: "", goal: "", strictness_level: "normal"
    });
    setStep(1);
    setMode(initialMode);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleLogin = async () => {
    setIsLoading(true);
    try {
      await login(formData.email, formData.password);
      toast.success("¡Bienvenido de nuevo!");
      onSuccess?.();
      handleClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al iniciar sesión");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async () => {
    setIsLoading(true);
    try {
      const profile = {
        weight: formData.weight ? parseFloat(formData.weight) : null,
        height: formData.height ? parseFloat(formData.height) : null,
        sex: formData.sex || null,
        allergies: formData.allergies,
        conditions: formData.conditions,
        activity_level: formData.activity_level || null,
        goal: formData.goal || null,
        strictness_level: formData.strictness_level || "normal"
      };
      await register(formData.name, formData.email, formData.password, profile);
      toast.success("¡Cuenta creada con éxito!");
      onSuccess?.();
      handleClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al registrarse");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleAllergy = (id) => {
    setFormData(prev => ({
      ...prev,
      allergies: prev.allergies.includes(id)
        ? prev.allergies.filter(a => a !== id)
        : [...prev.allergies, id]
    }));
  };

  const toggleCondition = (id) => {
    setFormData(prev => ({
      ...prev,
      conditions: prev.conditions.includes(id)
        ? prev.conditions.filter(c => c !== id)
        : [...prev.conditions, id]
    }));
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="bg-zinc-950 border-zinc-800 max-w-md mx-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold text-zinc-50 flex items-center gap-2">
            {mode === "login" ? (
              <><User className="w-5 h-5 text-green-500" /> Iniciar Sesión</>
            ) : (
              <><UserCircle className="w-5 h-5 text-green-500" /> 
                {step === 1 ? "Crear Cuenta" : step === 2 ? "Tu Perfil de Salud" : "Alergias y Condiciones"}
              </>
            )}
          </DialogTitle>
          <DialogDescription className="text-sm text-zinc-500">
            {mode === "login" 
              ? "Accede a tu cuenta para ver alertas personalizadas"
              : step === 1 
                ? "Crea tu cuenta para personalizar tu experiencia"
                : step === 2
                  ? "Esta información nos ayuda a darte alertas más precisas"
                  : "Selecciona tus alergias y condiciones de salud"
            }
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-4">
          {mode === "login" ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="email" className="text-zinc-300">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="tu@email.com"
                  className="bg-zinc-900 border-zinc-800 text-zinc-50"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  data-testid="login-email"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-zinc-300">Contraseña</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  className="bg-zinc-900 border-zinc-800 text-zinc-50"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  data-testid="login-password"
                />
              </div>
              <Button 
                onClick={handleLogin} 
                className="w-full bg-green-600 hover:bg-green-500"
                disabled={isLoading}
                data-testid="login-submit"
              >
                {isLoading ? "Iniciando..." : "Iniciar Sesión"}
              </Button>
              <p className="text-center text-sm text-zinc-500">
                ¿No tienes cuenta?{" "}
                <button 
                  onClick={() => { setMode("register"); setStep(1); }}
                  className="text-green-500 hover:underline"
                  data-testid="switch-to-register"
                >
                  Regístrate
                </button>
              </p>
            </>
          ) : (
            <>
              {step === 1 && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="name" className="text-zinc-300">Nombre</Label>
                    <Input
                      id="name"
                      placeholder="Tu nombre"
                      className="bg-zinc-900 border-zinc-800 text-zinc-50"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      data-testid="register-name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reg-email" className="text-zinc-300">Email</Label>
                    <Input
                      id="reg-email"
                      type="email"
                      placeholder="tu@email.com"
                      className="bg-zinc-900 border-zinc-800 text-zinc-50"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      data-testid="register-email"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reg-password" className="text-zinc-300">Contraseña</Label>
                    <Input
                      id="reg-password"
                      type="password"
                      placeholder="Mínimo 6 caracteres"
                      className="bg-zinc-900 border-zinc-800 text-zinc-50"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      data-testid="register-password"
                    />
                  </div>
                  <Button 
                    onClick={() => setStep(2)} 
                    className="w-full bg-green-600 hover:bg-green-500"
                    disabled={!formData.name || !formData.email || !formData.password}
                    data-testid="register-next-step"
                  >
                    Continuar
                  </Button>
                </>
              )}

              {step === 2 && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-zinc-300 flex items-center gap-1">
                        <Scale className="w-4 h-4" /> Peso (kg)
                      </Label>
                      <Input
                        type="number"
                        placeholder="70"
                        className="bg-zinc-900 border-zinc-800 text-zinc-50"
                        value={formData.weight}
                        onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
                        data-testid="register-weight"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-zinc-300 flex items-center gap-1">
                        <Ruler className="w-4 h-4" /> Altura (cm)
                      </Label>
                      <Input
                        type="number"
                        placeholder="170"
                        className="bg-zinc-900 border-zinc-800 text-zinc-50"
                        value={formData.height}
                        onChange={(e) => setFormData({ ...formData, height: e.target.value })}
                        data-testid="register-height"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-zinc-300 flex items-center gap-1">
                      <User className="w-4 h-4" /> Sexo
                    </Label>
                    <Select 
                      value={formData.sex} 
                      onValueChange={(value) => setFormData({ ...formData, sex: value })}
                    >
                      <SelectTrigger className="bg-zinc-900 border-zinc-800 text-zinc-50" data-testid="register-sex">
                        <SelectValue placeholder="Selecciona" />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-900 border-zinc-800">
                        <SelectItem value="male">Masculino</SelectItem>
                        <SelectItem value="female">Femenino</SelectItem>
                        <SelectItem value="other">Otro</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      onClick={() => setStep(1)} 
                      className="flex-1 border-zinc-700"
                    >
                      Atrás
                    </Button>
                    <Button 
                      onClick={() => setStep(3)} 
                      className="flex-1 bg-green-600 hover:bg-green-500"
                      data-testid="register-to-allergies"
                    >
                      Continuar
                    </Button>
                  </div>
                </>
              )}

              {step === 3 && (
                <>
                  <div className="space-y-3">
                    <Label className="text-zinc-300 flex items-center gap-1">
                      <AlertTriangle className="w-4 h-4 text-yellow-500" /> Alergias
                    </Label>
                    <div className="grid grid-cols-2 gap-2">
                      {ALLERGY_OPTIONS.map((allergy) => (
                        <div 
                          key={allergy.id}
                          className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors duration-200 ${
                            formData.allergies.includes(allergy.id)
                              ? "bg-yellow-500/10 border-yellow-500/50"
                              : "bg-zinc-900 border-zinc-800 hover:border-zinc-700"
                          }`}
                          onClick={() => toggleAllergy(allergy.id)}
                          data-testid={`allergy-${allergy.id}`}
                        >
                          <Checkbox 
                            checked={formData.allergies.includes(allergy.id)}
                            className="border-zinc-600"
                          />
                          <span className="text-sm text-zinc-300">{allergy.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label className="text-zinc-300 flex items-center gap-1">
                      <Heart className="w-4 h-4 text-red-500" /> Condiciones de Salud
                    </Label>
                    <div className="grid grid-cols-2 gap-2">
                      {CONDITION_OPTIONS.map((condition) => (
                        <div 
                          key={condition.id}
                          className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors duration-200 ${
                            formData.conditions.includes(condition.id)
                              ? "bg-red-500/10 border-red-500/50"
                              : "bg-zinc-900 border-zinc-800 hover:border-zinc-700"
                          }`}
                          onClick={() => toggleCondition(condition.id)}
                          data-testid={`condition-${condition.id}`}
                        >
                          <Checkbox 
                            checked={formData.conditions.includes(condition.id)}
                            className="border-zinc-600"
                          />
                          <span className="text-sm text-zinc-300">{condition.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      onClick={() => setStep(2)} 
                      className="flex-1 border-zinc-700"
                    >
                      Atrás
                    </Button>
                    <Button 
                      onClick={handleRegister} 
                      className="flex-1 bg-green-600 hover:bg-green-500"
                      disabled={isLoading}
                      data-testid="register-submit"
                    >
                      {isLoading ? "Creando..." : "Crear Cuenta"}
                    </Button>
                  </div>
                </>
              )}

              {step === 1 && (
                <p className="text-center text-sm text-zinc-500">
                  ¿Ya tienes cuenta?{" "}
                  <button 
                    onClick={() => setMode("login")}
                    className="text-green-500 hover:underline"
                    data-testid="switch-to-login"
                  >
                    Inicia sesión
                  </button>
                </p>
              )}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ==================== NAVBAR ====================
const Navbar = ({ onAuthClick, onProfileClick }) => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    toast.success("Sesión cerrada");
  };

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
        
        {user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button 
                className="flex items-center gap-2 p-2 rounded-lg hover:bg-zinc-800/50 transition-colors duration-200"
                data-testid="user-menu"
              >
                <div className="w-8 h-8 rounded-full bg-green-600/20 flex items-center justify-center">
                  <User className="w-4 h-4 text-green-500" />
                </div>
                <span className="text-sm text-zinc-300 hidden sm:block">{user.name}</span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="bg-zinc-900 border-zinc-800 w-48">
              <DropdownMenuItem 
                onClick={onProfileClick}
                className="text-zinc-300 focus:bg-zinc-800 cursor-pointer"
                data-testid="profile-menu-item"
              >
                <Settings className="w-4 h-4 mr-2" />
                Mi Perfil
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-zinc-800" />
              <DropdownMenuItem 
                onClick={handleLogout}
                className="text-red-400 focus:bg-zinc-800 cursor-pointer"
                data-testid="logout-menu-item"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Cerrar Sesión
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Button 
            onClick={onAuthClick}
            variant="outline"
            className="border-green-600 text-green-500 hover:bg-green-600/10"
            data-testid="login-button"
          >
            <User className="w-4 h-4 mr-2" />
            Entrar
          </Button>
        )}
      </div>
    </nav>
  );
};

// ==================== FOOTER ====================
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
            <a href="/privacy" className="text-zinc-500 hover:text-zinc-300 transition-colors duration-200" data-testid="footer-privacy-link">
              Política de Privacidad
            </a>
            <a href="/terms" className="text-zinc-500 hover:text-zinc-300 transition-colors duration-200" data-testid="footer-terms-link">
              Términos de Uso
            </a>
            <a href="/contact" className="text-zinc-500 hover:text-zinc-300 transition-colors duration-200" data-testid="footer-contact-link">
              Contacto
            </a>
          </div>
          
          <p className="text-xs text-zinc-600 text-center max-w-md">
            © {new Date().getFullYear()} NutriScan AI. Todos los derechos reservados.
          </p>
        </div>
      </div>
    </footer>
  );
};

// ==================== SCAN BUTTON ====================
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

// ==================== CAMERA MODAL ====================
const CameraModal = ({ isOpen, onClose, onCapture, isLoading }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        toast.error("Por favor, selecciona una imagen válida");
        return;
      }
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
      toast.error("Por favor, captura o sube una imagen primero");
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
          <DialogDescription className="text-sm text-zinc-500">
            Toma una foto de la etiqueta nutricional o súbela desde tu galería
          </DialogDescription>
        </DialogHeader>
        
        <div className="p-6 flex flex-col items-center gap-6">
          {/* Viewfinder */}
          <div className="viewfinder relative bg-zinc-900/50 flex items-center justify-center overflow-hidden">
            <div className="viewfinder-corner-tr" />
            <div className="viewfinder-corner-bl" />
            
            {previewUrl ? (
              <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" data-testid="image-preview" />
            ) : (
              <div className="text-center p-4">
                <Camera className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                <p className="text-sm text-zinc-500">Captura o sube la etiqueta nutricional</p>
              </div>
            )}
            
            {isLoading && <div className="scan-line animate-scan-line" />}
          </div>

          {/* Hidden inputs */}
          <input 
            ref={cameraInputRef}
            type="file" 
            accept="image/*" 
            capture="environment"
            onChange={handleFileSelect}
            className="hidden"
            data-testid="camera-input"
          />
          <input 
            ref={fileInputRef}
            type="file" 
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
            data-testid="file-input"
          />

          {/* Actions */}
          <div className="w-full flex flex-col gap-3">
            {!isLoading && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <Button 
                    onClick={() => cameraInputRef.current?.click()}
                    variant="outline" 
                    className="border-zinc-700 bg-zinc-900/50 hover:bg-zinc-800 text-zinc-300"
                    data-testid="open-camera-button"
                  >
                    <Camera className="w-4 h-4 mr-2" />
                    Cámara
                  </Button>
                  <Button 
                    onClick={() => fileInputRef.current?.click()}
                    variant="outline" 
                    className="border-zinc-700 bg-zinc-900/50 hover:bg-zinc-800 text-zinc-300"
                    data-testid="open-gallery-button"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Galería
                  </Button>
                </div>

                <Button 
                  onClick={handleCapture}
                  disabled={!selectedFile}
                  className="w-full bg-green-600 hover:bg-green-500 text-white neon-glow disabled:opacity-50"
                  data-testid="analyze-button"
                >
                  <ScanLine className="w-4 h-4 mr-2" />
                  Analizar Etiqueta
                </Button>
              </>
            )}

            {isLoading && (
              <div className="text-center py-4">
                <div className="loading-spinner animate-spin-slow mx-auto mb-4" />
                <p className="text-sm text-zinc-400 animate-pulse">Analizando con IA...</p>
                <p className="text-xs text-zinc-600 mt-2">Gemini 3 Flash está procesando la imagen</p>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ==================== NUTRIENT CARD ====================
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
    const iconMap = { 'Calorías': Flame, 'Grasas': Droplets, 'Carbohidratos': Cookie, 'Fibra': Wheat, 'Proteínas': Dna };
    const key = Object.keys(iconMap).find(k => name.toLowerCase().includes(k.toLowerCase()));
    return key ? iconMap[key] : Sparkles;
  };

  const Icon = getIcon(nutrient.name);

  return (
    <div className={`glass-light p-4 rounded-2xl opacity-0 animate-fade-in-up stagger-${Math.min(index + 1, 8)}`} data-testid={`nutrient-card-${nutrient.name.toLowerCase().replace(/\s+/g, '-')}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center ${getStatusColor(nutrient.status)}`}>
            <Icon className="w-4 h-4" />
          </div>
          <span className="text-sm text-zinc-400">{nutrient.name}</span>
        </div>
        {nutrient.percentage && <span className="text-xs text-zinc-500">{nutrient.percentage}% VD</span>}
      </div>
      <div className="flex items-end justify-between mb-2">
        <span className={`text-2xl font-bold ${getStatusColor(nutrient.status)}`}>{nutrient.value}</span>
        <span className="text-sm text-zinc-500">{nutrient.unit}</span>
      </div>
      {nutrient.percentage && (
        <div className="nutrient-bar">
          <div className={`nutrient-bar-fill ${getBarColor(nutrient.status)}`} style={{ width: `${Math.min(nutrient.percentage * 2, 100)}%` }} />
        </div>
      )}
    </div>
  );
};

// ==================== HEALTH SCORE ====================
const HealthScore = ({ score }) => {
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (score / 100) * circumference;
  const getScoreColor = (s) => s >= 80 ? '#22c55e' : s >= 60 ? '#eab308' : '#ef4444';
  const getScoreLabel = (s) => s >= 80 ? 'Excelente' : s >= 60 ? 'Bueno' : s >= 40 ? 'Regular' : 'Mejorable';

  return (
    <div className="health-score-circle flex items-center justify-center" data-testid="health-score">
      <svg className="progress-ring w-full h-full" viewBox="0 0 100 100">
        <circle className="health-score-bg" cx="50" cy="50" r="45" />
        <circle className="health-score-fill" cx="50" cy="50" r="45" stroke={getScoreColor(score)} strokeDasharray={circumference} strokeDashoffset={offset} transform="rotate(-90 50 50)" />
      </svg>
      <div className="absolute text-center">
        <span className="text-3xl font-bold" style={{ color: getScoreColor(score) }}>{score}</span>
        <p className="text-xs text-zinc-500 mt-1">{getScoreLabel(score)}</p>
      </div>
    </div>
  );
};

// ==================== PERSONALIZED ALERT ====================
const PersonalizedAlertCard = ({ alert }) => {
  const getStyles = (type) => {
    switch (type) {
      case "danger": return "bg-red-500/10 border-red-500/30 text-red-400";
      case "warning": return "bg-yellow-500/10 border-yellow-500/30 text-yellow-400";
      default: return "bg-blue-500/10 border-blue-500/30 text-blue-400";
    }
  };
  const getIcon = (type) => type === "danger" ? <AlertCircle className="w-5 h-5" /> : type === "warning" ? <AlertTriangle className="w-5 h-5" /> : <Info className="w-5 h-5" />;

  return (
    <div className={`p-4 rounded-xl border ${getStyles(alert.type)} flex items-start gap-3`} data-testid={`personalized-alert-${alert.type}`}>
      {getIcon(alert.type)}
      <p className="text-sm font-medium">{alert.message}</p>
    </div>
  );
};

// ==================== CHAT COMPONENT ====================
const ChatBubble = ({ message, isUser }) => {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div className={`max-w-[85%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div className={`flex items-end gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${isUser ? 'bg-green-600' : 'bg-zinc-700'}`}>
            {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-green-400" />}
          </div>
          <div className={`px-4 py-2.5 rounded-2xl ${isUser ? 'bg-green-600 text-white rounded-br-md' : 'bg-zinc-800 text-zinc-200 rounded-bl-md'}`}>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

const ProductChat = ({ analysisId, imageBase64, token }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Load chat history on mount
  useEffect(() => {
    const loadHistory = async () => {
      if (!token) return;
      try {
        const response = await axios.get(`${API}/chat/${analysisId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.data.messages?.length > 0) {
          setMessages(response.data.messages);
        }
      } catch (e) {
        console.error("Error loading chat history:", e);
      }
    };
    loadHistory();
  }, [analysisId, token]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = { role: "user", content: inputValue.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await axios.post(`${API}/chat`, {
        analysis_id: analysisId,
        message: userMessage.content,
        image_base64: imageBase64
      }, { headers });

      const assistantMessage = { role: "assistant", content: response.data.response };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      toast.error("Error al enviar el mensaje");
      // Remove the user message if failed
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const suggestedQuestions = [
    "¿Es saludable para mí?",
    "¿Puedo comerlo si estoy a dieta?",
    "¿Qué ingredientes son preocupantes?",
    "Dame alternativas más saludables"
  ];

  return (
    <Card className="bg-zinc-900/70 border-zinc-800 mt-6 overflow-hidden" data-testid="product-chat">
      {/* Header */}
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-zinc-800/50 transition-colors duration-200"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-green-600/20 flex items-center justify-center">
            <MessageCircle className="w-5 h-5 text-green-500" />
          </div>
          <div className="text-left">
            <h3 className="text-sm font-medium text-zinc-200">Chat con NutriScan AI</h3>
            <p className="text-xs text-zinc-500">Pregunta lo que quieras sobre este producto</p>
          </div>
        </div>
        <div className={`transform transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
          <ArrowLeft className="w-5 h-5 text-zinc-500 rotate-90" />
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-zinc-800">
          {/* Messages area */}
          <ScrollArea className="h-[300px] p-4">
            {messages.length === 0 ? (
              <div className="text-center py-8">
                <Bot className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                <p className="text-sm text-zinc-500 mb-4">¡Hola! Pregúntame sobre este producto</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => { setInputValue(q); inputRef.current?.focus(); }}
                      className="text-xs px-3 py-1.5 rounded-full bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-300 transition-colors duration-200"
                      data-testid={`suggested-question-${i}`}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg, index) => (
                  <ChatBubble key={index} message={msg} isUser={msg.role === 'user'} />
                ))}
                {isLoading && (
                  <div className="flex justify-start mb-3">
                    <div className="flex items-end gap-2">
                      <div className="w-7 h-7 rounded-full bg-zinc-700 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-green-400" />
                      </div>
                      <div className="px-4 py-3 rounded-2xl rounded-bl-md bg-zinc-800">
                        <div className="flex gap-1">
                          <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
                          <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                          <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </ScrollArea>

          {/* Input area */}
          <div className="p-4 border-t border-zinc-800 bg-zinc-900/50">
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Escribe tu pregunta..."
                className="flex-1 bg-zinc-800 border-zinc-700 text-zinc-200 placeholder:text-zinc-500"
                disabled={isLoading}
                data-testid="chat-input"
              />
              <Button
                onClick={sendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="bg-green-600 hover:bg-green-500 px-4"
                data-testid="chat-send"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};

// ==================== RESULTS VIEW ====================
const ResultsView = ({ result, onBack, imageBase64 }) => {
  const { token } = useAuth();
  
  if (!result) return null;

  return (
    <div className="min-h-screen bg-zinc-950 pt-20 pb-8 px-4" data-testid="results-view">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-4 mb-8 opacity-0 animate-fade-in-up">
          <button onClick={onBack} className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 transition-colors duration-200" data-testid="back-button">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-zinc-50 font-['Manrope']">Resultado del Análisis</h1>
            <p className="text-sm text-zinc-500">Analizado con Gemini 3 Flash</p>
          </div>
        </div>

        {/* Personalized Alerts */}
        {result.personalized_alerts?.length > 0 && (
          <div className="mb-6 space-y-3 opacity-0 animate-fade-in-up">
            <h3 className="text-sm font-medium text-zinc-400 flex items-center gap-2 px-1">
              <Shield className="w-4 h-4 text-green-500" />
              Alertas Personalizadas para Ti
            </h3>
            {result.personalized_alerts.map((alert, index) => (
              <PersonalizedAlertCard key={index} alert={alert} />
            ))}
          </div>
        )}

        {/* Product Info */}
        <Card className="bg-zinc-900/50 border-zinc-800 mb-6 opacity-0 animate-fade-in-up stagger-1">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="w-20 h-20 rounded-xl bg-zinc-800 flex items-center justify-center">
                <Cookie className="w-10 h-10 text-zinc-600" />
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-zinc-50" data-testid="product-name">{result.product_name}</h2>
                <p className="text-sm text-zinc-500" data-testid="product-brand">{result.brand}</p>
                <Badge variant="outline" className="mt-2 text-xs border-zinc-700 text-zinc-400">{result.serving_size}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Health Score */}
        <div className="glass rounded-2xl p-6 mb-6 flex flex-col items-center opacity-0 animate-fade-in-up stagger-2">
          <h3 className="text-sm font-medium text-zinc-400 mb-4">Puntuación de Salud</h3>
          <HealthScore score={result.health_score} />
        </div>

        {/* Nutrients */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-zinc-400 mb-4 px-1">Información Nutricional</h3>
          <div className="grid grid-cols-2 gap-3">
            {result.nutrients.map((nutrient, index) => (
              <NutrientCard key={nutrient.name} nutrient={nutrient} index={index} />
            ))}
          </div>
        </div>

        {/* Ingredients */}
        {result.ingredients?.length > 0 && (
          <Card className="bg-zinc-900/50 border-zinc-800 mb-6 opacity-0 animate-fade-in-up stagger-5">
            <CardContent className="p-4">
              <h3 className="text-sm font-medium text-zinc-400 mb-3">Ingredientes</h3>
              <p className="text-sm text-zinc-500 leading-relaxed">{result.ingredients.join(", ")}</p>
            </CardContent>
          </Card>
        )}

        {/* Warnings */}
        {result.warnings?.length > 0 && (
          <Card className="bg-yellow-500/5 border-yellow-500/20 mb-6 opacity-0 animate-fade-in-up stagger-6">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-yellow-500" />
                <h3 className="text-sm font-medium text-yellow-500">Advertencias</h3>
              </div>
              <ul className="space-y-2">
                {result.warnings.map((warning, index) => (
                  <li key={index} className="text-sm text-zinc-400 flex items-start gap-2" data-testid={`warning-${index}`}>
                    <span className="text-yellow-500 mt-1">•</span>{warning}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Recommendations */}
        {result.recommendations?.length > 0 && (
          <Card className="bg-green-500/5 border-green-500/20 opacity-0 animate-fade-in-up stagger-7">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <h3 className="text-sm font-medium text-green-500">Recomendaciones</h3>
              </div>
              <ul className="space-y-2">
                {result.recommendations.map((rec, index) => (
                  <li key={index} className="text-sm text-zinc-400 flex items-start gap-2" data-testid={`recommendation-${index}`}>
                    <span className="text-green-500 mt-1">•</span>{rec}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* AI Chat */}
        <ProductChat analysisId={result.id} imageBase64={imageBase64} token={token} />

        <div className="mt-8 flex justify-center">
          <Button onClick={onBack} className="bg-green-600 hover:bg-green-500 text-white px-8 neon-glow" data-testid="new-scan-button">
            <Camera className="w-4 h-4 mr-2" />
            Nuevo Escaneo
          </Button>
        </div>
      </div>
    </div>
  );
};

// ==================== PROFILE MODAL ====================
const ProfileModal = ({ isOpen, onClose }) => {
  const { user, updateProfile } = useAuth();
  const [formData, setFormData] = useState({
    name: "", weight: "", height: "", sex: "", allergies: [], conditions: []
  });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || "",
        weight: user.profile?.weight || "",
        height: user.profile?.height || "",
        sex: user.profile?.sex || "",
        allergies: user.profile?.allergies || [],
        conditions: user.profile?.conditions || []
      });
    }
  }, [user]);

  const toggleAllergy = (id) => setFormData(prev => ({
    ...prev, allergies: prev.allergies.includes(id) ? prev.allergies.filter(a => a !== id) : [...prev.allergies, id]
  }));

  const toggleCondition = (id) => setFormData(prev => ({
    ...prev, conditions: prev.conditions.includes(id) ? prev.conditions.filter(c => c !== id) : [...prev.conditions, id]
  }));

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await updateProfile({
        name: formData.name,
        profile: {
          weight: formData.weight ? parseFloat(formData.weight) : null,
          height: formData.height ? parseFloat(formData.height) : null,
          sex: formData.sex || null,
          allergies: formData.allergies,
          conditions: formData.conditions
        }
      });
      toast.success("Perfil actualizado");
      onClose();
    } catch (error) {
      toast.error("Error al actualizar el perfil");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-zinc-950 border-zinc-800 max-w-md mx-auto max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold text-zinc-50 flex items-center gap-2">
            <Settings className="w-5 h-5 text-green-500" /> Mi Perfil
          </DialogTitle>
          <DialogDescription className="text-sm text-zinc-500">
            Actualiza tu información para recibir alertas personalizadas
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 pt-4">
          <div className="space-y-2">
            <Label className="text-zinc-300">Nombre</Label>
            <Input value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="bg-zinc-900 border-zinc-800 text-zinc-50" data-testid="profile-name" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-zinc-300 flex items-center gap-1"><Scale className="w-4 h-4" /> Peso (kg)</Label>
              <Input type="number" value={formData.weight} onChange={(e) => setFormData({ ...formData, weight: e.target.value })} className="bg-zinc-900 border-zinc-800 text-zinc-50" data-testid="profile-weight" />
            </div>
            <div className="space-y-2">
              <Label className="text-zinc-300 flex items-center gap-1"><Ruler className="w-4 h-4" /> Altura (cm)</Label>
              <Input type="number" value={formData.height} onChange={(e) => setFormData({ ...formData, height: e.target.value })} className="bg-zinc-900 border-zinc-800 text-zinc-50" data-testid="profile-height" />
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-zinc-300">Sexo</Label>
            <Select value={formData.sex} onValueChange={(value) => setFormData({ ...formData, sex: value })}>
              <SelectTrigger className="bg-zinc-900 border-zinc-800 text-zinc-50" data-testid="profile-sex">
                <SelectValue placeholder="Selecciona" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-800">
                <SelectItem value="male">Masculino</SelectItem>
                <SelectItem value="female">Femenino</SelectItem>
                <SelectItem value="other">Otro</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-3">
            <Label className="text-zinc-300 flex items-center gap-1">
              <AlertTriangle className="w-4 h-4 text-yellow-500" /> Alergias
            </Label>
            <div className="grid grid-cols-2 gap-2">
              {ALLERGY_OPTIONS.map((allergy) => (
                <div key={allergy.id} className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors duration-200 ${formData.allergies.includes(allergy.id) ? "bg-yellow-500/10 border-yellow-500/50" : "bg-zinc-900 border-zinc-800 hover:border-zinc-700"}`} onClick={() => toggleAllergy(allergy.id)}>
                  <Checkbox checked={formData.allergies.includes(allergy.id)} className="border-zinc-600" />
                  <span className="text-sm text-zinc-300">{allergy.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <Label className="text-zinc-300 flex items-center gap-1">
              <Heart className="w-4 h-4 text-red-500" /> Condiciones de Salud
            </Label>
            <div className="grid grid-cols-2 gap-2">
              {CONDITION_OPTIONS.map((condition) => (
                <div key={condition.id} className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors duration-200 ${formData.conditions.includes(condition.id) ? "bg-red-500/10 border-red-500/50" : "bg-zinc-900 border-zinc-800 hover:border-zinc-700"}`} onClick={() => toggleCondition(condition.id)}>
                  <Checkbox checked={formData.conditions.includes(condition.id)} className="border-zinc-600" />
                  <span className="text-sm text-zinc-300">{condition.label}</span>
                </div>
              ))}
            </div>
          </div>

          <Button onClick={handleSave} className="w-full bg-green-600 hover:bg-green-500" disabled={isLoading} data-testid="profile-save">
            {isLoading ? "Guardando..." : "Guardar Cambios"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ==================== HOME PAGE ====================
const Home = () => {
  const { user, token, loading } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleCapture = async (imageBase64) => {
    setIsLoading(true);
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await axios.post(`${API}/analyze`, { image_base64: imageBase64 }, { headers });
      setAnalysisResult(response.data);
      setIsCameraOpen(false);
      toast.success('¡Análisis completado!', { description: 'La etiqueta ha sido analizada con Gemini 3 Flash' });
    } catch (error) {
      console.error('Error analyzing label:', error);
      toast.error('Error al analizar', { description: error.response?.data?.detail || 'No se pudo completar el análisis' });
    } finally {
      setIsLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="loading-spinner animate-spin-slow" />
      </div>
    );
  }

  if (analysisResult) {
    return (
      <>
        <Navbar onAuthClick={() => setShowAuthModal(true)} onProfileClick={() => setShowProfileModal(true)} />
        <ResultsView result={analysisResult} onBack={() => setAnalysisResult(null)} />
        <Footer />
        <ProfileModal isOpen={showProfileModal} onClose={() => setShowProfileModal(false)} />
        <Toaster position="top-center" richColors />
      </>
    );
  }

  return (
    <>
      <Navbar onAuthClick={() => setShowAuthModal(true)} onProfileClick={() => setShowProfileModal(true)} />
      
      <main className="hero-bg min-h-screen flex flex-col" data-testid="home-page">
        <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 pt-24 pb-16">
          {user && (
            <div className="mb-6 opacity-0 animate-fade-in">
              <Badge className="bg-green-600/20 text-green-400 border-green-600/30">
                <User className="w-3 h-3 mr-1" />
                Hola, {user.name}
              </Badge>
            </div>
          )}

          <div className="text-center max-w-lg mx-auto mb-12 opacity-0 animate-fade-in-up">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6 font-['Manrope']">
              <span className="gradient-text">Escanea</span>
              <br />
              <span className="text-zinc-50">tu alimentación</span>
            </h1>
            <p className="text-base text-zinc-400 leading-relaxed max-w-md mx-auto">
              Analiza las etiquetas nutricionales con inteligencia artificial y recibe alertas personalizadas según tu perfil de salud.
            </p>
          </div>

          <div className="mb-8 opacity-0 animate-fade-in-up stagger-2">
            <ScanButton onClick={() => setIsCameraOpen(true)} />
          </div>

          <p className="text-sm text-zinc-500 animate-bounce-subtle opacity-0 animate-fade-in stagger-3">
            Toca para escanear una etiqueta
          </p>

          <div className="grid grid-cols-3 gap-4 mt-16 max-w-md w-full opacity-0 animate-fade-in-up stagger-4">
            <div className="text-center">
              <div className="w-12 h-12 rounded-xl bg-zinc-900/80 border border-zinc-800 flex items-center justify-center mx-auto mb-2">
                <Zap className="w-5 h-5 text-green-500" />
              </div>
              <p className="text-xs text-zinc-500">Análisis<br/>con IA</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 rounded-xl bg-zinc-900/80 border border-zinc-800 flex items-center justify-center mx-auto mb-2">
                <Shield className="w-5 h-5 text-green-500" />
              </div>
              <p className="text-xs text-zinc-500">Alertas<br/>Personalizadas</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 rounded-xl bg-zinc-900/80 border border-zinc-800 flex items-center justify-center mx-auto mb-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
              </div>
              <p className="text-xs text-zinc-500">Recomendaciones<br/>Saludables</p>
            </div>
          </div>

          {!user && (
            <div className="mt-12 opacity-0 animate-fade-in-up stagger-5">
              <Card className="bg-zinc-900/30 border-zinc-800 max-w-sm">
                <CardContent className="p-4 text-center">
                  <Shield className="w-8 h-8 text-green-500 mx-auto mb-2" />
                  <p className="text-sm text-zinc-400 mb-3">
                    Crea una cuenta para recibir alertas basadas en tus alergias y condiciones de salud
                  </p>
                  <Button onClick={() => setShowAuthModal(true)} variant="outline" className="border-green-600 text-green-500 hover:bg-green-600/10" data-testid="cta-register">
                    Crear Cuenta Gratis
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </main>

      <Footer />
      <CameraModal isOpen={isCameraOpen} onClose={() => setIsCameraOpen(false)} onCapture={handleCapture} isLoading={isLoading} />
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} onSuccess={() => {}} initialMode="login" />
      <ProfileModal isOpen={showProfileModal} onClose={() => setShowProfileModal(false)} />
      <Toaster position="top-center" richColors toastOptions={{ style: { background: '#18181b', border: '1px solid #27272a', color: '#fafafa' } }} />
    </>
  );
};

// ==================== APP ====================
function App() {
  return (
    <AuthProvider>
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
    </AuthProvider>
  );
}

export default App;
