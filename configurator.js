// ... (everything before parseModels remains same)

function parseModels(modelsStr) {
    if (!modelsStr) return [];
    // Try to parse as JSON array first
    try {
        const parsed = JSON.parse(modelsStr);
        if (Array.isArray(parsed)) {
            return parsed.map(m => {
                if (typeof m === 'string') return { id: m.trim(), name: m.trim() };
                if (m && typeof m === 'object') return { id: m.id, name: m.name || m.id };
                return null;
            }).filter(Boolean);
        }
    } catch (e) {
        // Not JSON, treat as comma-separated list
    }
    // Fallback: split by comma and trim
    return modelsStr.split(',').map(id => ({ id: id.trim(), name: id.trim() })).filter(m => m.id);
}
