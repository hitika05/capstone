import React, { useRef } from 'react';
import { Download, ChevronLeft, CheckCircle, Phone, Mail } from 'lucide-react';
import html2canvas from 'html2canvas';

const DesignViewer = ({ imageUrl, businessName, tagline, services, contact, cta, layoutType, brandColor, accentColor, textContrast, isGenerating, onBack, uiText, rawImageMode = false }) => {
  const templateRef = useRef(null);
  const text = uiText || {
    generating: 'Generating your masterpiece...',
    download: 'Download Final Image',
    noImage: 'No image generated yet.',
    back: 'Back'
  };

  // --- RUTHLESS HALLUCINATION FILTER ---
  const isHallucinated = (value) => {
    if (!value) return true;
    const text = String(value).trim();
    const lower = text.toLowerCase();

    // Clear placeholder emails/domains.
    if (/\b(?:info|contact|hello|test)@(?:example|placeholder|sample)\.(?:com|org|net)\b/i.test(lower)) {
      return true;
    }

    if (lower.includes('placeholder') || lower.includes('generic') || lower.includes('dummy')) {
      return true;
    }

    // Treat as placeholder only when all digits are repeated/synthetic patterns.
    const digits = text.replace(/\D/g, '');
    if (digits.length >= 7) {
      if (/^(\d)\1+$/.test(digits)) return true;
      if (digits.startsWith('1234567') || digits.startsWith('9876543') || digits.startsWith('0123456')) return true;
    }

    return false;
  };

  const finalContact = isHallucinated(contact) ? "" : contact;
  const displayServices = Array.isArray(services) ? services.filter(Boolean).slice(0, 5) : [];
  const contactParts = finalContact
    ? finalContact.split('|').map((part) => part.trim()).filter(Boolean)
    : [];

  const renderContact = () => {
    if (!contactParts.length) return null;
    return (
      <div className="template-contact-list">
        {contactParts.map((part, idx) => {
          const isEmail = part.includes('@');
          return (
            <div key={`${part}-${idx}`} className="template-contact-item">
              {isEmail ? <Mail size={16} /> : <Phone size={16} />}
              <span>{part}</span>
            </div>
          );
        })}
      </div>
    );
  };

  // --- CONTEXTUAL BRANDING ---
  // If no name found, use high-end generic branding
  const finalBusinessName = businessName || "Your Brand";
  
  // --- SEMANTIC LAYOUT OVERRIDE ---
  const finalLayout = layoutType;
  const totalTextLoad = (
    String(finalBusinessName || '').length +
    String(tagline || '').length +
    String(cta || '').length +
    displayServices.join(' ').length +
    String(finalContact || '').length
  );
  const densityClass = totalTextLoad > 110 ? 'density-compact' : 'density-regular';

  const handleDownload = async () => {
    if (!templateRef.current) return;
    try {
      const canvas = await html2canvas(templateRef.current, {
        useCORS: true,
        scale: 2,
        logging: false,
        backgroundColor: null
      });
      const link = document.createElement('a');
      link.download = `${businessName || 'design'}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const handleShare = async () => {
    if (!templateRef.current) return;
    try {
      const canvas = await html2canvas(templateRef.current, {
        useCORS: true,
        scale: 2,
        logging: false,
        backgroundColor: null
      });

      const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
      if (!blob) return;

      if (navigator.share && navigator.canShare) {
        const file = new File([blob], `${businessName || 'design'}.png`, { type: 'image/png' });
        if (navigator.canShare({ files: [file] })) {
          await navigator.share({ title: businessName || 'Design', files: [file] });
          return;
        }
      }

      // Fallback: download when native share is unavailable.
      const link = document.createElement('a');
      link.download = `${businessName || 'design'}-shared.png`;
      link.href = URL.createObjectURL(blob);
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (err) {
      console.error('Share failed:', err);
    }
  };

  return (
    <div className="design-viewer-container">
      {imageUrl || isGenerating ? (
        <>
          {isGenerating ? (
            <div className="template-wrapper" style={{display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#1e293b'}}>
              <div className="loader"></div>
              <p style={{marginLeft: '1rem'}}>{text.generating}</p>
            </div>
          ) : (
            <div 
              className={`template-wrapper layout-${finalLayout} text-${textContrast} ${densityClass}`} 
              ref={templateRef} 
              data-layout={finalLayout}
              style={{
                '--brand-color': brandColor,
                '--accent-color': accentColor
              }}
            >
              <img
                src={imageUrl}
                alt="Background"
                className="template-bg-image"
                crossOrigin="anonymous"
                onError={(event) => {
                  event.currentTarget.style.display = 'none';
                }}
              />
              {!rawImageMode && <div className="template-overlay"></div>}
              {rawImageMode && (
                <div style={{position: 'absolute', inset: 0, zIndex: 3}} />
              )}
              
              {/* LAYOUT: ELEGANT (Luxury centered) */}
              {!rawImageMode && finalLayout === 'elegant' && (
                <div className="template-content layout-elegant">
                  <div className="glass-container">
                    <h2 className="template-title">{finalBusinessName}</h2>
                    {tagline && <p className="template-tagline">{tagline}</p>}
                    {displayServices.length > 0 && (
                      <div className="template-services">
                        {displayServices.map((svc, i) => (
                          <div key={i} className="service-item">
                            <CheckCircle size={16} color="var(--accent-color)" />
                            <span>{svc}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  {(cta || finalContact) && (
                    <div className="template-footer">
                      {cta && <div className="template-cta">{cta}</div>}
                      {renderContact()}
                    </div>
                  )}
                </div>
              )}

              {/* LAYOUT: BOLD (Impact banners) */}
              {!rawImageMode && finalLayout === 'bold' && (
                <div className="template-content layout-bold">
                  <div className="bold-header">
                    <h2 className="template-title">{finalBusinessName}</h2>
                    {tagline && <div className="tagline-ribbon">{tagline}</div>}
                  </div>
                  <div className="bold-body">
                    {displayServices.length > 0 && (
                      <div className="template-services">
                        {displayServices.map((svc, i) => (
                          <div key={i} className="service-pill">{svc}</div>
                        ))}
                      </div>
                    )}
                  </div>
                  {(cta || finalContact) && (
                    <div className="template-footer">
                      {cta && <div className="template-cta">{cta}</div>}
                      {renderContact()}
                    </div>
                  )}
                </div>
              )}

              {/* LAYOUT: SIDEBAR (Fashion boutique) */}
              {!rawImageMode && finalLayout === 'sidebar' && (
                <div className="template-content layout-sidebar">
                  <div className="sidebar-strip">
                    <h2 className="template-title">{finalBusinessName}</h2>
                    {tagline && <p className="template-tagline">{tagline}</p>}
                    <div className="divider" />
                    {displayServices.length > 0 && (
                      <div className="template-services">
                        {displayServices.map((svc, i) => (
                          <div key={i} className="sidebar-service">{svc}</div>
                        ))}
                      </div>
                    )}
                  </div>
                  {(cta || finalContact) && (
                    <div className="template-footer" style={{padding: '0 8% 8%'}}>
                      {cta && <div className="template-cta">{cta}</div>}
                      {renderContact()}
                    </div>
                  )}
                </div>
              )}

              {/* LAYOUT: MINIMAL (Modern card) */}
              {!rawImageMode && finalLayout === 'minimal' && (
                <div className="template-content layout-minimal">
                  <div className="minimal-top">
                    {tagline && <span className="minimal-tagline">{tagline}</span>}
                  </div>
                  <div className="minimal-bottom">
                    {(finalBusinessName || cta) && (
                      <div className="minimal-bar">
                        <h2 className="template-title">{finalBusinessName}</h2>
                        {cta && <div className="v-divider" />}
                        {cta && <span className="minimal-cta">{cta}</span>}
                      </div>
                    )}
                  </div>
                  {finalContact && (
                    <div className="template-footer" style={{paddingBottom: '8%'}}>
                      {renderContact()}
                    </div>
                  )}
                </div>
              )}

            </div>
          )}

          <div style={{display: 'flex', gap: '1rem', width: '100%', marginTop: '1.5rem'}}>
             <button className="btn btn-secondary" style={{padding: '0.875rem 1rem'}} onClick={onBack} title={text.back}>
              <ChevronLeft size={20} />
            </button>
            <button onClick={handleShare} className="btn btn-secondary" style={{padding: '0.875rem 1rem'}}>
              Share
            </button>
            <button 
              onClick={handleDownload}
              className="btn btn-primary" 
              style={{flex: 1}}
            >
              <Download size={20} />
              {text.download}
            </button>
          </div>
        </>
      ) : (
        <div style={{height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <p>{text.noImage}</p>
        </div>
      )}
    </div>
  );
};

export default DesignViewer;
