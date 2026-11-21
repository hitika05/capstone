import React, { useState } from 'react';
import { Mic, CheckCircle, ChevronRight, Palette, Sparkles, ArrowRight } from 'lucide-react';
import AudioRecorder from './components/AudioRecorder';
import DesignViewer from './components/DesignViewer';
import axios from 'axios';
import './index.css';
import heroBg from './assets/hero-bg.jpg';
import stickerChai from './assets/sticker-chai.png';
import stickerFlower from './assets/sticker-flower.png';
import stickerTailor from './assets/sticker-tailor.png';
import stickerSweets from './assets/sticker-sweets.png';

const API_BASE = 'http://127.0.0.1:8000';

const LOCALES = {
  en: {
    headerSub: 'Voice-to-Instagram Post Generator',
    homeSpeakLabel: 'I will speak in:',
    homeOverlayLabel: 'Text on image should be in:',
    startRecording: 'Start Recording',
    back: 'Back',
    reviewEdit: 'Review & Edit',
    transcribedTitle: 'Transcribed Text:',
    voiceGuideTitle: 'What to include in your audio:',
    voiceGuideText: 'Speak business name, services/products, color/theme preference, any offers, and phone/email if you want them on the design.',
    reviewTitle: 'Review & Edit Details',
    businessName: 'Business Name',
    tagline: 'Tagline',
    taglinePlaceholder: 'e.g., Quality & Excellence',
    services: 'Services/Features',
    addService: '+ Add Service',
    contact: 'Contact (Phone/Email)',
    contactPlaceholder: 'e.g., +91 98765 43210 | hello@brand.com',
    cta: 'Call to Action',
    ctaPlaceholder: 'e.g., Order Now',
    confirmPreview: 'Confirm & Preview',
    modeLabel: 'Generation Mode',
    modeDesign: 'Design Post',
    modePriceList: 'Price List',
    generatePriceList: 'Generate Price List',
    priceGuideTitle: 'What to include for price list:',
    priceGuideText: 'Speak business name and list items with prices, for example: Tea 20, Coffee 40, Sandwich 80.',
    priceInputLabel: 'Price List Items',
    priceInputPlaceholder: 'e.g., Monalisa Beauty Parlour | Facial 499, Cleanup 299, Hair Spa 799',
    themeLabel: 'Theme Selection (Output Preview)',
    themeHint: 'Compare themes by clicking each option and choose the best one.',
    elegant: 'Elegant (Luxury)',
    bold: 'Bold (Impact)',
    sidebar: 'Sidebar (Fashion)',
    minimal: 'Minimal (Modern)',
    errorTranscribe: 'Failed to transcribe audio. ',
    errorExtract: 'Failed to extract details. ',
    recorder: {
      start: 'Start Recording',
      stop: 'Stop Recording',
      processing: 'Processing audio...',
      recording: 'Recording! Click to stop.',
      idle: 'Click mic to record your prompt',
      micError: 'Microphone access denied or not available. Please allow microphone permissions and try again.'
    },
    viewer: {
      generating: 'Generating your masterpiece...',
      download: 'Download Final Image',
      noImage: 'No image generated yet.',
      back: 'Back'
    }
  },
  hi: {
    headerSub: 'आवाज़ से इंस्टाग्राम पोस्ट जनरेटर',
    homeSpeakLabel: 'मैं किस भाषा में बोलूंगा/बोलूंगी:',
    homeOverlayLabel: 'इमेज पर टेक्स्ट किस भाषा में चाहिए:',
    startRecording: 'रिकॉर्डिंग शुरू करें',
    back: 'वापस',
    reviewEdit: 'जाँचें और संपादित करें',
    transcribedTitle: 'ट्रांसक्राइब किया गया टेक्स्ट:',
    voiceGuideTitle: 'ऑडियो में क्या बोलना है:',
    voiceGuideText: 'अपना बिज़नेस नाम, सेवाएँ/प्रोडक्ट, रंग या थीम पसंद, ऑफर और यदि चाहिए तो फोन/ईमेल ज़रूर बोलें।',
    reviewTitle: 'विवरण जाँचें और संपादित करें',
    businessName: 'बिज़नेस नाम',
    tagline: 'टैगलाइन',
    taglinePlaceholder: 'उदा: गुणवत्ता और भरोसा',
    services: 'सेवाएँ/हाइलाइट्स',
    addService: '+ सेवा जोड़ें',
    contact: 'संपर्क (फोन/ईमेल)',
    contactPlaceholder: 'उदा: +91 98765 43210 | hello@brand.com',
    cta: 'कॉल टू एक्शन',
    ctaPlaceholder: 'उदा: अभी ऑर्डर करें',
    confirmPreview: 'पुष्टि करें और प्रीव्यू देखें',
    modeLabel: 'जनरेशन मोड',
    modeDesign: 'डिज़ाइन पोस्ट',
    modePriceList: 'प्राइस लिस्ट',
    generatePriceList: 'प्राइस लिस्ट जनरेट करें',
    priceGuideTitle: 'प्राइस लिस्ट के लिए क्या बोलें:',
    priceGuideText: 'बिज़नेस नाम और आइटम के साथ कीमत बोलें, जैसे: चाय 20, कॉफी 40, सैंडविच 80।',
    priceInputLabel: 'प्राइस लिस्ट आइटम्स',
    priceInputPlaceholder: 'उदा: मोनालिसा ब्यूटी पार्लर | फेशियल 499, क्लीनअप 299, हेयर स्पा 799',
    themeLabel: 'थीम चयन (आउटपुट प्रीव्यू)',
    themeHint: 'हर थीम पर क्लिक करके तुलना करें और सबसे बेहतर चुनें।',
    elegant: 'एलिगेंट (लक्ज़री)',
    bold: 'बोल्ड (इम्पैक्ट)',
    sidebar: 'साइडबार (फैशन)',
    minimal: 'मिनिमल (मॉडर्न)',
    errorTranscribe: 'ऑडियो ट्रांसक्राइब नहीं हो पाया। ',
    errorExtract: 'डिटेल्स निकालने में समस्या हुई। ',
    recorder: {
      start: 'रिकॉर्डिंग शुरू करें',
      stop: 'रिकॉर्डिंग रोकें',
      processing: 'ऑडियो प्रोसेस हो रहा है...',
      recording: 'रिकॉर्डिंग चालू है! रोकने के लिए क्लिक करें।',
      idle: 'अपना प्रॉम्प्ट रिकॉर्ड करने के लिए माइक दबाएं',
      micError: 'माइक्रोफोन एक्सेस नहीं मिला। कृपया अनुमति दें और फिर प्रयास करें।'
    },
    viewer: {
      generating: 'आपका डिजाइन बनाया जा रहा है...',
      download: 'अंतिम इमेज डाउनलोड करें',
      noImage: 'अभी तक कोई इमेज जनरेट नहीं हुई है।',
      back: 'वापस'
    }
  },
  mr: {
    headerSub: 'आवाजेतून इंस्टाग्राम पोस्ट जनरेटर',
    homeSpeakLabel: 'मी कोणत्या भाषेत बोलेन:',
    homeOverlayLabel: 'इमेजवरील मजकूर कोणत्या भाषेत हवा:',
    startRecording: 'रेकॉर्डिंग सुरू करा',
    back: 'मागे',
    reviewEdit: 'तपासा आणि संपादित करा',
    transcribedTitle: 'ट्रान्सक्राइब केलेला मजकूर:',
    voiceGuideTitle: 'ऑडिओमध्ये काय बोलावे:',
    voiceGuideText: 'आपले व्यवसाय नाव, सेवा/प्रॉडक्ट, रंग किंवा थीम, ऑफर्स आणि हवे असल्यास फोन/ईमेल नक्की सांगा।',
    reviewTitle: 'माहिती तपासा आणि संपादित करा',
    businessName: 'व्यवसायाचे नाव',
    tagline: 'टॅगलाइन',
    taglinePlaceholder: 'उदा: गुणवत्ता आणि विश्वास',
    services: 'सेवा/हायलाइट्स',
    addService: '+ सेवा जोडा',
    contact: 'संपर्क (फोन/ईमेल)',
    contactPlaceholder: 'उदा: +91 98765 43210 | hello@brand.com',
    cta: 'कॉल टू अॅक्शन',
    ctaPlaceholder: 'उदा: आत्ताच ऑर्डर करा',
    confirmPreview: 'पुष्टी करा आणि प्रीव्यू पहा',
    modeLabel: 'जनरेशन मोड',
    modeDesign: 'डिझाइन पोस्ट',
    modePriceList: 'प्राइस लिस्ट',
    generatePriceList: 'प्राइस लिस्ट जनरेट करा',
    priceGuideTitle: 'प्राइस लिस्टसाठी काय बोलावे:',
    priceGuideText: 'व्यवसायाचे नाव आणि पदार्थासोबत किंमत बोला, उदा: चहा 20, कॉफी 40, सँडविच 80.',
    priceInputLabel: 'प्राइस लिस्ट आयटम्स',
    priceInputPlaceholder: 'उदा: मोनालिसा ब्युटी पार्लर | फेशियल 499, क्लीनअप 299, हेअर स्पा 799',
    themeLabel: 'थीम निवड (आउटपुट प्रीव्यू)',
    themeHint: 'प्रत्येक थीम क्लिक करून तुलना करा आणि सर्वोत्तम निवडा.',
    elegant: 'एलिगंट (लक्झरी)',
    bold: 'बोल्ड (इम्पॅक्ट)',
    sidebar: 'साइडबार (फॅशन)',
    minimal: 'मिनिमल (मॉडर्न)',
    errorTranscribe: 'ऑडिओ ट्रान्सक्राइब करता आला नाही. ',
    errorExtract: 'तपशील काढताना अडचण आली. ',
    recorder: {
      start: 'रेकॉर्डिंग सुरू करा',
      stop: 'रेकॉर्डिंग थांबवा',
      processing: 'ऑडिओ प्रक्रिया सुरू आहे...',
      recording: 'रेकॉर्डिंग सुरू आहे! थांबवण्यासाठी क्लिक करा.',
      idle: 'आपला प्रॉम्प्ट रेकॉर्ड करण्यासाठी माइक क्लिक करा',
      micError: 'मायक्रोफोन प्रवेश नाकारला गेला. कृपया परवानगी द्या आणि पुन्हा प्रयत्न करा.'
    },
    viewer: {
      generating: 'तुमचा डिझाइन तयार केला जात आहे...',
      download: 'अंतिम इमेज डाउनलोड करा',
      noImage: 'अजून इमेज जनरेट झालेली नाही.',
      back: 'मागे'
    }
  }
};

function App() {
  const [screen, setScreen] = useState('home'); // home, voice, review, output, research
  const [transcribedText, setTranscribedText] = useState('');
  const [spokenLang, setSpokenLang] = useState('en-US');
  const [overlayLang, setOverlayLang] = useState('English');
  const [userId] = useState('demo_user_1');
  
  // Review screen states
  const [editedData, setEditedData] = useState(null);
  const [parsedIntent, setParsedIntent] = useState(null);
  const [variants, setVariants] = useState([]);
  const [refinementCommand, setRefinementCommand] = useState('');
  
  // Output display states
  const [imageUrl, setImageUrl] = useState('');
  const [businessName, setBusinessName] = useState('');
  const [tagline, setTagline] = useState('');
  const [services, setServices] = useState([]);
  const [contact, setContact] = useState('');
  const [cta, setCta] = useState('');
  const [layoutType, setLayoutType] = useState('elegant');
  const [brandColor, setBrandColor] = useState('#6366f1');
  const [accentColor, setAccentColor] = useState('#fbbf24');
  const [textContrast, setTextContrast] = useState('light');
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);

  const uiLang = spokenLang === 'hi-IN' ? 'hi' : spokenLang === 'mr-IN' ? 'mr' : 'en';
  const t = LOCALES[uiLang];
  const themeOptions = [
    { value: 'elegant', label: t.elegant },
    { value: 'bold', label: t.bold },
    { value: 'sidebar', label: t.sidebar },
    { value: 'minimal', label: t.minimal }
  ];

  const resolveUsableImageUrl = (candidateUrl, fallbackUrl) => {
    return new Promise((resolve) => {
      if (!candidateUrl) {
        resolve(fallbackUrl || '');
        return;
      }

      const probe = new Image();
      const timeoutId = setTimeout(() => resolve(fallbackUrl || ''), 5000);

      probe.onload = () => {
        clearTimeout(timeoutId);
        resolve(candidateUrl);
      };

      probe.onerror = () => {
        clearTimeout(timeoutId);
        resolve(fallbackUrl || '');
      };

      probe.src = candidateUrl;
    });
  };

  const handleAudioComplete = async (audioBlob) => {
    try {
      setIsGenerating(true);
      setError(null);
      
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      formData.append('spoken_lang', spokenLang);
      
      const res = await axios.post(`${API_BASE}/speech-to-text`, formData);
      setTranscribedText(res.data.text);
      setIsGenerating(false);
    } catch (err) {
      const errorMsg = err.response?.data?.detail 
        ? (typeof err.response.data.detail === 'object' ? JSON.stringify(err.response.data.detail) : err.response.data.detail) 
        : err.message;
      setError(t.errorTranscribe + errorMsg);
      setIsGenerating(false);
    }
  };

  const handleExtractAndReview = async () => {
    try {
      setIsGenerating(true);
      setError(null);

      // Stage 3 review parse: lightweight keyword intent parser.
      const intentRes = await axios.post(`${API_BASE}/parse-intent`, {
        text: transcribedText,
        mode: 'review',
        user_id: userId
      });
      setParsedIntent(intentRes.data.intent || null);

      // Draft generation for review screen.
      const res = await axios.post(`${API_BASE}/generate-design`, {
        prompt: transcribedText,
        overlay_lang: overlayLang,
        user_id: userId,
        final_submission: false,
        parsed_intent: intentRes.data.intent || null
      });
      
      // Store the extracted data for review
      const data = {
        business_name: res.data.business_name || '',
        tagline: res.data.tagline || '',
        services: res.data.services || [],
        contact: res.data.contact || '',
        cta: res.data.cta || '',
        layout_type: res.data.layout_type || 'elegant',
        brand_color: res.data.brand_color || '#6366f1',
        accent_color: res.data.accent_color || '#fbbf24',
        text_contrast: res.data.text_contrast || 'light'
      };
      
      setEditedData(JSON.parse(JSON.stringify(data))); // Deep copy
      setImageUrl(res.data.image_url);
      setVariants(res.data.variants || []);
      setScreen('review');
      setIsGenerating(false);
    } catch (err) {
      const errorMsg = err.response?.data?.detail 
        ? (typeof err.response.data.detail === 'object' ? JSON.stringify(err.response.data.detail) : err.response.data.detail) 
        : err.message;
      setError(t.errorExtract + errorMsg);
      setIsGenerating(false);
    }
  };

  const handleConfirmReview = async () => {
    try {
      setIsGenerating(true);
      setError(null);

      const approvedServiceList = (editedData.services || []).filter(Boolean).join(', ');
      const approvedPrompt = [
        transcribedText,
        `approved business name: ${editedData.business_name || ''}`,
        `approved tagline: ${editedData.tagline || ''}`,
        `approved services: ${approvedServiceList}`,
        `approved contact: ${editedData.contact || ''}`,
        `approved cta: ${editedData.cta || ''}`,
        `approved layout: ${editedData.layout_type || 'elegant'}`,
        `approved brand color: ${editedData.brand_color || ''}`,
        `approved accent color: ${editedData.accent_color || ''}`,
        'preserve original background scene from transcript and keep a rich real-world product background, never plain/empty/flat',
        'use all approved details exactly and do not omit any service/contact in final design'
      ].join(' | ');

      await axios.post(`${API_BASE}/brand-memory/save`, {
        user_id: userId,
        profile: {
          business_name: editedData.business_name,
          tagline: editedData.tagline,
          brand_color: editedData.brand_color,
          accent_color: editedData.accent_color,
          style: editedData.layout_type,
          contact: editedData.contact
        }
      });

      // Stage 3 final parse + Stage 6 A/B variants on final submission.
      const finalRes = await axios.post(`${API_BASE}/generate-design`, {
        prompt: approvedPrompt,
        overlay_lang: overlayLang,
        user_id: userId,
        final_submission: true,
        parsed_intent: parsedIntent
      });

      setVariants(finalRes.data.variants || []);
      const usableImageUrl = await resolveUsableImageUrl(finalRes.data.image_url, imageUrl);
      setImageUrl(usableImageUrl);
      setParsedIntent(finalRes.data.intent || parsedIntent);

      // Apply reviewed edits as final overlay content.
      setBusinessName(editedData.business_name);
      setTagline(editedData.tagline);
      setServices(editedData.services);
      setContact(editedData.contact);
      setCta(editedData.cta);
      setLayoutType(editedData.layout_type || 'elegant');
      setBrandColor(editedData.brand_color);
      setAccentColor(editedData.accent_color);
      setTextContrast(editedData.text_contrast);
      setScreen('output');
      setIsGenerating(false);
    } catch (err) {
      const errorMsg = err.response?.data?.detail
        ? (typeof err.response.data.detail === 'object' ? JSON.stringify(err.response.data.detail) : err.response.data.detail)
        : err.message;
      setError(t.errorExtract + errorMsg);
      setIsGenerating(false);
    }
  };

  const handleRefineDesign = async () => {
    if (!refinementCommand.trim()) return;
    try {
      setIsGenerating(true);
      setError(null);

      const refinedRes = await axios.post(`${API_BASE}/refine-design`, {
        prompt: transcribedText,
        refinement_command: refinementCommand,
        overlay_lang: overlayLang,
        user_id: userId,
        parsed_intent: parsedIntent
      });

      setVariants(refinedRes.data.variants || []);
      setImageUrl(refinedRes.data.image_url || imageUrl);
      setRefinementCommand('');
      setIsGenerating(false);
    } catch (err) {
      const errorMsg = err.response?.data?.detail
        ? (typeof err.response.data.detail === 'object' ? JSON.stringify(err.response.data.detail) : err.response.data.detail)
        : err.message;
      setError(t.errorExtract + errorMsg);
      setIsGenerating(false);
    }
  };

  const selectVariant = async (variant) => {
    setImageUrl(variant.image_url);
    try {
      if (parsedIntent) {
        await axios.post(`${API_BASE}/variant-choice`, {
          user_id: userId,
          chosen_variant: variant.variant_id,
          intent: parsedIntent
        });
      }
    } catch (err) {
      // Non-blocking analytics path.
      console.warn('Variant choice logging failed', err);
    }
  };

  const updateEditedData = (field, value) => {
    setEditedData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const updateServiceItem = (index, value) => {
    const newServices = [...editedData.services];
    newServices[index] = value;
    setEditedData(prev => ({
      ...prev,
      services: newServices
    }));
  };

  const removeServiceItem = (index) => {
    setEditedData(prev => ({
      ...prev,
      services: prev.services.filter((_, i) => i !== index)
    }));
  };

  const addServiceItem = () => {
    setEditedData(prev => ({
      ...prev,
      services: [...prev.services, 'New Service']
    }));
  };

  const floatingStickers = [
    { src: stickerChai, alt: 'Chai stall', className: 'sticker sticker-chai' },
    { src: stickerFlower, alt: 'Flower shop', className: 'sticker sticker-flower' },
    { src: stickerTailor, alt: 'Tailor shop', className: 'sticker sticker-tailor' },
    { src: stickerSweets, alt: 'Sweet shop', className: 'sticker sticker-sweets' }
  ];

  return (
    <div className="app-root">
      {screen === 'home' && (
        <>
          <nav className="ref-nav">
            <div className="ref-nav-inner">
              <div className="ref-brand">
                <div className="ref-brand-icon">
                  <Mic size={18} />
                </div>
                <span>VoiceDesign AI</span>
              </div>
              <div className="ref-nav-links">
                <a href="#features">Features</a>
                <a href="#how">How It Works</a>
              </div>
              <button className="ref-try-btn">Try Free</button>
            </div>
          </nav>

          <section className="ref-hero">
            <img src={heroBg} alt="" className="ref-hero-bg" />
            <div className="ref-hero-overlay" />

            {floatingStickers.map((sticker) => (
              <div key={sticker.alt} className={sticker.className}>
                <img src={sticker.src} alt={sticker.alt} />
              </div>
            ))}

            <div className="ref-hero-content">
              <div className="hero-badge">
                <Sparkles size={14} />
                <span>Voice-First Design for Everyone</span>
              </div>
              <h1>
                Bolo, Design Karo. <span className="gradient-text">Apni Bhasha Mein.</span>
              </h1>
              <p>
                Create stunning logos, flyers and social media posts by simply speaking in Hindi or Marathi. No English. No design skills. Just your voice.
              </p>

              <div className="ref-hero-actions">
                <button className="ref-main-cta" onClick={() => setScreen('voice')}>
                  <Mic size={20} />
                  Start Designing with Voice
                </button>
                <button className="ref-ghost-cta" onClick={() => setScreen('voice')}>
                  See How It Works
                  <ArrowRight size={18} />
                </button>
              </div>

              <div className="lang-strip">
                <div className="lang-item">
                  <label>{t.homeSpeakLabel}</label>
                  <select
                    value={spokenLang}
                    onChange={e => {
                      const val = e.target.value;
                      setSpokenLang(val);
                      if (val === 'hi-IN') setOverlayLang('Hindi');
                      else if (val === 'mr-IN') setOverlayLang('Marathi');
                      else setOverlayLang('English');
                    }}
                  >
                    <option value="en-US">English</option>
                    <option value="hi-IN">Hindi / हिंदी</option>
                    <option value="mr-IN">Marathi / मराठी</option>
                  </select>
                </div>
                <div className="lang-item">
                  <label>{t.homeOverlayLabel}</label>
                  <select value={overlayLang} onChange={e => setOverlayLang(e.target.value)}>
                    <option value="English">English</option>
                    <option value="Hindi">Hindi / हिंदी</option>
                    <option value="Marathi">Marathi / मराठी</option>
                  </select>
                </div>
              </div>

              <div className="voice-bars">
                {Array.from({ length: 24 }).map((_, i) => (
                  <span
                    key={i}
                    style={{
                      animationDelay: `${i * 0.05}s`,
                      height: `${10 + (i % 6) * 6}px`
                    }}
                  />
                ))}
              </div>
            </div>
          </section>
        </>
      )}

      {screen !== 'home' && (
        <div className="app-container app-shell">
          <div className="header reveal-up" style={{animationDelay: '0.08s'}}>
            <h1>VoiceDesign AI</h1>
            <p>{t.headerSub}</p>
          </div>

          <div className="card reveal-up" style={{animationDelay: '0.14s'}}>
            {error && <div style={{width: '100%', padding: '1rem', background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', borderRadius: '0.5rem', border: '1px solid #ef4444'}}>{error}</div>}

            {screen === 'voice' && (
              <>
                <AudioRecorder onComplete={handleAudioComplete} isProcessing={isGenerating} uiText={t.recorder} />

                <div className="text-display" style={{background: 'rgba(15, 23, 42, 0.45)', border: '1px solid rgba(148, 163, 184, 0.35)'}}>
                  <strong>{t.voiceGuideTitle}</strong>
                  <p style={{marginTop: '0.55rem', color: 'var(--text-muted)'}}>{t.voiceGuideText}</p>
                </div>

                {transcribedText && (
                  <div className="text-display">
                    <strong>{t.transcribedTitle}</strong>
                    <p style={{marginTop: '0.5rem', color: 'var(--text-muted)'}}>{transcribedText}</p>
                  </div>
                )}

                <div style={{display: 'flex', gap: '1rem', width: '100%', marginTop: '1rem'}}>
                  <button className="btn btn-secondary" style={{flex: 1}} onClick={() => setScreen('home')}>{t.back}</button>
                  <button
                    className="btn btn-primary"
                    style={{flex: 1}}
                    onClick={handleExtractAndReview}
                    disabled={!transcribedText || isGenerating}
                  >
                    {isGenerating ? <span className="loader"></span> : <ChevronRight size={20} />}
                    {t.reviewEdit}
                  </button>
                </div>
              </>
            )}

            {screen === 'review' && editedData && (
              <>
                <div style={{width: '100%'}}>
                  <h3 style={{marginBottom: '1.5rem', fontSize: '1.1rem', color: 'var(--text-main)'}}>{t.reviewTitle}</h3>

                  {parsedIntent && (
                    <div className="text-display" style={{marginBottom: '1rem'}}>
                      <strong>Intent Parser Output</strong>
                      <p style={{marginTop: '0.5rem', color: 'var(--text-muted)'}}>
                        {`${parsedIntent.design_type || ''} | ${parsedIntent.business || ''} | ${parsedIntent.color || 'no-color'} | ${parsedIntent.mood || ''}`}
                      </p>
                    </div>
                  )}

                  <div style={{display: 'flex', flexDirection: 'column', gap: '1.2rem'}}>
                    <div>
                      <label style={{fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem'}}>{t.businessName}</label>
                      <input
                        type="text"
                        value={editedData.business_name}
                        onChange={(e) => updateEditedData('business_name', e.target.value)}
                        style={{width: '100%', padding: '0.7rem', borderRadius: '0.5rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid rgba(255, 255, 255, 0.1)', fontFamily: 'inherit'}}
                      />
                    </div>

                    <div>
                      <label style={{fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem'}}>{t.tagline}</label>
                      <input
                        type="text"
                        value={editedData.tagline}
                        onChange={(e) => updateEditedData('tagline', e.target.value)}
                        placeholder={t.taglinePlaceholder}
                        style={{width: '100%', padding: '0.7rem', borderRadius: '0.5rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid rgba(255, 255, 255, 0.1)', fontFamily: 'inherit'}}
                      />
                    </div>

                    <div>
                      <label style={{fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem'}}>{t.services}</label>
                      <div style={{display: 'flex', flexDirection: 'column', gap: '0.6rem'}}>
                        {editedData.services.map((service, idx) => (
                          <div key={idx} style={{display: 'flex', gap: '0.5rem'}}>
                            <input
                              type="text"
                              value={service}
                              onChange={(e) => updateServiceItem(idx, e.target.value)}
                              style={{flex: 1, padding: '0.7rem', borderRadius: '0.5rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid rgba(255, 255, 255, 0.1)', fontFamily: 'inherit'}}
                            />
                            <button
                              onClick={() => removeServiceItem(idx)}
                              style={{padding: '0.7rem 1rem', background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', border: '1px solid rgba(239, 68, 68, 0.5)', borderRadius: '0.5rem', cursor: 'pointer'}}
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                      <button
                        onClick={addServiceItem}
                        style={{marginTop: '0.5rem', padding: '0.6rem 1rem', background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', border: '1px solid rgba(99, 102, 241, 0.5)', borderRadius: '0.5rem', cursor: 'pointer', fontSize: '0.9rem'}}
                      >
                        {t.addService}
                      </button>
                    </div>

                    <div>
                      <label style={{fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem'}}>{t.contact}</label>
                      <input
                        type="text"
                        value={editedData.contact}
                        onChange={(e) => updateEditedData('contact', e.target.value)}
                        placeholder={t.contactPlaceholder}
                        style={{width: '100%', padding: '0.7rem', borderRadius: '0.5rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid rgba(255, 255, 255, 0.1)', fontFamily: 'inherit'}}
                      />
                    </div>

                    <div>
                      <label style={{fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem'}}>{t.cta}</label>
                      <input
                        type="text"
                        value={editedData.cta}
                        onChange={(e) => updateEditedData('cta', e.target.value)}
                        placeholder={t.ctaPlaceholder}
                        style={{width: '100%', padding: '0.7rem', borderRadius: '0.5rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid rgba(255, 255, 255, 0.1)', fontFamily: 'inherit'}}
                      />
                    </div>
                  </div>
                </div>

                <div style={{display: 'flex', gap: '1rem', width: '100%', marginTop: '2rem'}}>
                  <button className="btn btn-secondary" style={{flex: 1}} onClick={() => setScreen('voice')}>{t.back}</button>
                  <button
                    className="btn btn-primary"
                    style={{flex: 1}}
                    onClick={handleConfirmReview}
                    disabled={isGenerating}
                  >
                    {isGenerating ? <span className="loader"></span> : <CheckCircle size={20} />}
                    {isGenerating ? (uiLang === 'en' ? 'Generating...' : (uiLang === 'hi' ? 'जनरेट हो रहा है...' : 'जनरेट होत आहे...')) : t.confirmPreview}
                  </button>
                </div>
              </>
            )}

            {screen === 'output' && (
              <>
                {variants.length > 1 && (
                  <div className="inputs-group" style={{marginBottom: '0.5rem'}}>
                    <label style={{fontSize: '0.9rem', color: 'var(--text-main)', fontWeight: 700}}>A/B Variants</label>
                    <div style={{display: 'flex', gap: '0.5rem', flexWrap: 'wrap'}}>
                      {variants.map((variant) => (
                        <button
                          key={variant.variant_id}
                          onClick={() => selectVariant(variant)}
                          className="btn btn-secondary"
                          style={{padding: '0.45rem 0.75rem', fontSize: '0.78rem'}}
                        >
                          {variant.variant_id}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {(
                <div className="inputs-group" style={{marginBottom: '0.5rem'}}>
                  <label style={{fontSize: '0.9rem', color: 'var(--text-main)', fontWeight: 700}}>Refinement Command</label>
                  <input
                    type="text"
                    value={refinementCommand}
                    onChange={(e) => setRefinementCommand(e.target.value)}
                    placeholder={uiLang === 'en' ? 'e.g., background badal, logo bigger, cleaner text space' : (uiLang === 'hi' ? 'उदा: बैकग्राउंड बदलो, लोगो बड़ा, टेक्स्ट साफ' : 'उदा: पार्श्वभूमी बदला, लोगो मोठा, मजकूर स्पष्ट')}
                    style={{width: '100%', padding: '0.7rem', borderRadius: '0.5rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid rgba(255, 255, 255, 0.1)', fontFamily: 'inherit'}}
                  />
                  <button
                    className="btn btn-secondary"
                    onClick={handleRefineDesign}
                    disabled={isGenerating || !refinementCommand.trim()}
                    style={{marginTop: '0.5rem'}}
                  >
                    Regenerate with Refinement
                  </button>
                </div>
                )}

                {(
                <div className="inputs-group" style={{marginBottom: '0.5rem'}}>
                  <label style={{fontSize: '0.9rem', color: 'var(--text-main)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.45rem'}}>
                    <Palette size={16} /> {t.themeLabel}
                  </label>
                  <p style={{fontSize: '0.82rem', color: 'var(--text-muted)'}}>{t.themeHint}</p>
                  <select
                    value={layoutType}
                    onChange={(e) => setLayoutType(e.target.value)}
                    style={{width: '100%', padding: '0.75rem', borderRadius: '0.5rem', background: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid rgba(255, 255, 255, 0.1)'}}
                  >
                    {themeOptions.map((theme) => (
                      <option key={theme.value} value={theme.value}>{theme.label}</option>
                    ))}
                  </select>
                  <div style={{display: 'flex', gap: '0.5rem', flexWrap: 'wrap'}}>
                    {themeOptions.map((theme) => (
                      <button
                        key={theme.value}
                        onClick={() => setLayoutType(theme.value)}
                        className="btn btn-secondary"
                        style={{
                          padding: '0.45rem 0.75rem',
                          borderColor: layoutType === theme.value ? 'var(--primary)' : 'rgba(255,255,255,0.2)',
                          background: layoutType === theme.value ? 'rgba(99,102,241,0.25)' : 'rgba(255,255,255,0.08)',
                          fontSize: '0.78rem'
                        }}
                      >
                        {theme.label}
                      </button>
                    ))}
                  </div>
                </div>
                )}

                <DesignViewer
                  imageUrl={imageUrl}
                  businessName={businessName}
                  tagline={tagline}
                  services={services}
                  contact={contact}
                  cta={cta}
                  layoutType={layoutType}
                  brandColor={brandColor}
                  accentColor={accentColor}
                  textContrast={textContrast}
                  isGenerating={isGenerating}
                  rawImageMode={false}
                  onBack={() => setScreen('review')}
                  uiText={t.viewer}
                />
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
