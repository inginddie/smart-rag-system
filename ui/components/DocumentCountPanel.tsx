import React, { useEffect, useState } from 'react';

interface DocumentCountPanelProps {
  fetchDocumentCount: () => Promise<number>;
}

const DocumentCountPanel: React.FC<DocumentCountPanelProps> = ({ fetchDocumentCount }) => {
  const [count, setCount] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCount = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetchDocumentCount();
        setCount(result);
      } catch (err) {
        setError('Error al cargar el número de documentos');
      } finally {
        setLoading(false);
      }
    };
    loadCount();
  }, [fetchDocumentCount]);

  return (
    <div style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px', maxWidth: '300px', textAlign: 'center' }}>
      <h3>Número total de documentos procesados</h3>
      {loading && <p>Cargando...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {count !== null && !loading && !error && (
        <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#007acc' }}>{count}</p>
      )}
    </div>
  );
};

export default DocumentCountPanel;
