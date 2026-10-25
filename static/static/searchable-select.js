/**
 * Searchable Select Dropdown Component
 * 
 * Creates a dropdown that shows all options on click, and filters as you type.
 * - Click/focus: Shows all options (text is selected for easy replacement)
 * - Type: Clears and filters the list
 * - Select: Sets value and closes
 * - Escape/blur: Closes and restores selected value
 */

// Helper function for escaping HTML
function _ssEscapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function _ssEscapeAttr(str) {
    return String(str || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/**
 * Initialize a searchable select with simple string options
 * @param {Object} config
 * @param {string} config.inputId - ID of the visible text input
 * @param {string} config.hiddenId - ID of the hidden input that stores the value
 * @param {string} config.dropdownId - ID of the dropdown container
 * @param {string[]} config.options - Array of option strings
 * @param {string} config.placeholder - Placeholder text
 * @param {Function} config.onChange - Callback when value changes
 * @param {string} config.emptyLabel - Label to show for empty string option (default: "(All)")
 */
function initSearchableSelect(config) {
    const { inputId, hiddenId, dropdownId, options, placeholder, onChange, emptyLabel } = config;
    const input = document.getElementById(inputId);
    const hidden = document.getElementById(hiddenId);
    const dropdown = document.getElementById(dropdownId);
    if (!input || !hidden || !dropdown) return null;
    
    let _options = [...options];
    let isOpen = false;
    let highlightIdx = -1;
    let filteredOptions = [..._options];
    let isFiltering = false;
    const _emptyLabel = emptyLabel || '(All)';
    
    function renderOptions(filter = '') {
        const filterLower = filter.toLowerCase().trim();
        filteredOptions = (filterLower && isFiltering)
            ? _options.filter(opt => opt.toLowerCase().includes(filterLower))
            : [..._options];
        
        if (filteredOptions.length === 0) {
            dropdown.innerHTML = '<div class="searchable-select-empty">No matches found</div>';
        } else {
            dropdown.innerHTML = filteredOptions.map((opt, i) => {
                const isSelected = opt === hidden.value;
                const isHighlighted = i === highlightIdx;
                const displayText = opt === '' ? _emptyLabel : opt;
                return `<div class="searchable-select-option${isSelected ? ' selected' : ''}${isHighlighted ? ' highlighted' : ''}" data-value="${_ssEscapeAttr(opt)}" data-idx="${i}">${_ssEscapeHtml(displayText)}</div>`;
            }).join('');
        }
        highlightIdx = -1;
    }
    
    function open() {
        isOpen = true;
        isFiltering = false;
        dropdown.classList.add('open');
        input.value = '';
        renderOptions('');
    }
    
    function close() {
        isOpen = false;
        dropdown.classList.remove('open');
        highlightIdx = -1;
        isFiltering = false;
        const val = hidden.value;
        input.value = val === '' ? '' : val;
    }
    
    function selectValue(val) {
        hidden.value = val;
        input.value = val === '' ? '' : val;
        isFiltering = false;
        close();
        if (onChange) onChange(val);
    }
    
    input.addEventListener('focus', () => {
        if (_options.length === 0) return;
        open();
        requestAnimationFrame(() => input.select());
    });
    
    input.addEventListener('input', () => {
        isFiltering = true;
        if (!isOpen) open();
        renderOptions(input.value);
    });
    
    input.addEventListener('blur', () => {
        setTimeout(() => close(), 200);
    });
    
    input.addEventListener('keydown', (e) => {
        if (!isOpen) {
            if (e.key === 'ArrowDown' || e.key === 'Enter') {
                open();
                e.preventDefault();
            }
            return;
        }
        
        if (e.key === 'ArrowDown') {
            highlightIdx = Math.min(highlightIdx + 1, filteredOptions.length - 1);
            renderOptions(isFiltering ? input.value : '');
            e.preventDefault();
        } else if (e.key === 'ArrowUp') {
            highlightIdx = Math.max(highlightIdx - 1, 0);
            renderOptions(isFiltering ? input.value : '');
            e.preventDefault();
        } else if (e.key === 'Enter' && highlightIdx >= 0 && filteredOptions[highlightIdx] !== undefined) {
            selectValue(filteredOptions[highlightIdx]);
            e.preventDefault();
        } else if (e.key === 'Escape') {
            close();
            e.preventDefault();
        }
    });
    
    dropdown.addEventListener('mousedown', (e) => {
        const opt = e.target.closest('.searchable-select-option');
        if (opt) {
            selectValue(opt.getAttribute('data-value'));
            e.preventDefault();
        }
    });
    
    input.placeholder = placeholder || 'Type to search...';
    
    return {
        setOptions: (newOptions) => {
            _options = [...newOptions];
            if (isOpen) renderOptions(isFiltering ? input.value : '');
        },
        setValue: (val) => {
            hidden.value = val;
            input.value = val;
        },
        getValue: () => hidden.value,
        clear: () => {
            hidden.value = '';
            input.value = '';
        }
    };
}

/**
 * Initialize a searchable select with separate display labels and values
 * @param {Object} config
 * @param {string} config.inputId - ID of the visible text input
 * @param {string} config.hiddenId - ID of the hidden input that stores the value
 * @param {string} config.dropdownId - ID of the dropdown container
 * @param {string[]} config.options - Array of display labels
 * @param {string[]} config.values - Array of values (same length as options)
 * @param {string} config.placeholder - Placeholder text
 * @param {Function} config.onChange - Callback when value changes
 */
function initSearchableSelectWithValues(config) {
    const { inputId, hiddenId, dropdownId, options, values, placeholder, onChange } = config;
    const input = document.getElementById(inputId);
    const hidden = document.getElementById(hiddenId);
    const dropdown = document.getElementById(dropdownId);
    if (!input || !hidden || !dropdown) return null;
    
    let _options = [...options];
    let _values = [...values];
    let isOpen = false;
    let highlightIdx = -1;
    let filteredIndices = [];
    let isFiltering = false;
    
    function renderOptions(filter = '') {
        const filterLower = filter.toLowerCase().trim();
        filteredIndices = [];
        
        for (let i = 0; i < _options.length; i++) {
            if ((!filterLower || !isFiltering) || _options[i].toLowerCase().includes(filterLower)) {
                filteredIndices.push(i);
            }
        }
        
        if (filteredIndices.length === 0) {
            dropdown.innerHTML = '<div class="searchable-select-empty">No matches found</div>';
        } else {
            dropdown.innerHTML = filteredIndices.map((idx, fi) => {
                const isSelected = _values[idx] === hidden.value;
                const isHighlighted = fi === highlightIdx;
                return `<div class="searchable-select-option${isSelected ? ' selected' : ''}${isHighlighted ? ' highlighted' : ''}" data-value="${_ssEscapeAttr(_values[idx])}" data-idx="${fi}">${_ssEscapeHtml(_options[idx])}</div>`;
            }).join('');
        }
        highlightIdx = -1;
    }
    
    function open() {
        isOpen = true;
        isFiltering = false;
        dropdown.classList.add('open');
        input.value = '';
        renderOptions('');
    }
    
    function close() {
        isOpen = false;
        dropdown.classList.remove('open');
        highlightIdx = -1;
        isFiltering = false;
        const idx = _values.indexOf(hidden.value);
        input.value = idx >= 0 ? _options[idx] : hidden.value;
    }
    
    function selectValue(val) {
        hidden.value = val;
        const idx = _values.indexOf(val);
        input.value = idx >= 0 ? _options[idx] : val;
        isFiltering = false;
        close();
        if (onChange) onChange(val);
    }
    
    input.addEventListener('focus', () => {
        if (_options.length === 0) return;
        open();
        requestAnimationFrame(() => input.select());
    });
    
    input.addEventListener('input', () => {
        isFiltering = true;
        if (!isOpen) open();
        renderOptions(input.value);
    });
    
    input.addEventListener('blur', () => {
        setTimeout(() => close(), 200);
    });
    
    input.addEventListener('keydown', (e) => {
        if (!isOpen) {
            if (e.key === 'ArrowDown' || e.key === 'Enter') {
                open();
                e.preventDefault();
            }
            return;
        }
        
        if (e.key === 'ArrowDown') {
            highlightIdx = Math.min(highlightIdx + 1, filteredIndices.length - 1);
            renderOptions(isFiltering ? input.value : '');
            e.preventDefault();
        } else if (e.key === 'ArrowUp') {
            highlightIdx = Math.max(highlightIdx - 1, 0);
            renderOptions(isFiltering ? input.value : '');
            e.preventDefault();
        } else if (e.key === 'Enter' && highlightIdx >= 0 && filteredIndices[highlightIdx] !== undefined) {
            selectValue(_values[filteredIndices[highlightIdx]]);
            e.preventDefault();
        } else if (e.key === 'Escape') {
            close();
            e.preventDefault();
        }
    });
    
    dropdown.addEventListener('mousedown', (e) => {
        const opt = e.target.closest('.searchable-select-option');
        if (opt) {
            selectValue(opt.getAttribute('data-value'));
            e.preventDefault();
        }
    });
    
    input.placeholder = placeholder || 'Type to search...';
    
    return {
        setOptions: (newOptions, newValues) => {
            _options = [...newOptions];
            _values = [...newValues];
            if (isOpen) renderOptions(isFiltering ? input.value : '');
        },
        setValue: (val) => {
            hidden.value = val;
            const idx = _values.indexOf(val);
            input.value = idx >= 0 ? _options[idx] : val;
        },
        getValue: () => hidden.value,
        clear: () => {
            hidden.value = '';
            input.value = '';
        }
    };
}

/**
 * Helper to create the HTML structure for a searchable select
 * @param {string} id - Base ID for the component
 * @param {string} placeholder - Placeholder text
 * @returns {string} HTML string
 */
function createSearchableSelectHTML(id, placeholder) {
    return `<div class="searchable-select-wrap" id="${id}-wrap">
        <input type="text" class="searchable-select-input" id="${id}-input" placeholder="${_ssEscapeAttr(placeholder || 'Type to filter...')}" autocomplete="off">
        <input type="hidden" id="${id}" value="">
        <div class="searchable-select-dropdown" id="${id}-dropdown"></div>
    </div>`;
}
