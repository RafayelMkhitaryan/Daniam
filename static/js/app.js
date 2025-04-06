const API_BASE_URL = 'http://localhost:8000'; // Update if your API is hosted elsewhere

// Store current role
let currentRole = '';

// Role change handler
function changeRole() {
    const roleSelect = document.getElementById('role-select');
    currentRole = roleSelect.value;
    
    // Hide all role-specific elements
    document.querySelectorAll('.role1-only, .role2-only, .role3-only').forEach(el => {
        el.style.display = 'none';
    });
    
    // Show elements for selected role
    if (currentRole) {
        document.querySelectorAll('.' + currentRole + '-only').forEach(el => {
            el.style.display = 'block';
        });
        
        // Open the first tab for this role
        const firstTab = document.querySelector('.' + currentRole + '-only.tab-btn');
        if (firstTab) {
            firstTab.click();
        }
    }
}

// Tab functionality
function openTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');
}

async function createTable() {
    if (currentRole !== 'role1') {
        displayResult('create-result', 'Error: You need role1 permission');
        return;
    }
    
    const tableName = document.getElementById('new-table-name').value;
    const messageSpan = document.getElementById('create-message');
    
    // Check if table name is empty
    if (!tableName || tableName.trim() === '') {
        messageSpan.textContent = 'Please enter a table name!';
        messageSpan.style.color = '#e74c3c'; // Error color
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/create_table`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                table_name: tableName, 
                username: currentRole 
            })
        });
    
        const data = await response.json();
        
        if (!response.ok) {
            if (data.detail && data.detail.includes('already exists')) {
                messageSpan.textContent = `Table '${tableName}' already exists!`;
            } else {
                messageSpan.textContent = data.detail || 'Failed to create table';
            }
            messageSpan.style.color = '#e74c3c'; // Error color
            return;
        }
    
        messageSpan.textContent = data.message;
        messageSpan.style.color = '#27ae60'; // Success color
        
        // Clear the input field
        document.getElementById('new-table-name').value = '';
        
        // Clear the message after 3 seconds
        setTimeout(() => {
            messageSpan.textContent = '';
        }, 3000);
    } catch (error) {
        messageSpan.textContent = 'Error: ' + error.message;
        messageSpan.style.color = '#e74c3c'; // Error color
    }
}

async function insertData() {
    if (currentRole !== 'role1') {
        displayResult('insert-result', 'Error: You need role1 permission');
        return;
    }

    const tableName = document.getElementById('table-name-insert-data').value.trim();
    const name = document.getElementById('name').value.trim();
    const age = document.getElementById('age').value.trim();
    const messageSpan = document.getElementById('insert-message');

    // Validate inputs
    if (!tableName || !name || !age) {
        messageSpan.textContent = 'Please fill in all fields!';
        messageSpan.style.color = '#e74c3c';
        return;
    }

    // Validate name (must not be empty after trimming)
    if (name.length === 0) {
        messageSpan.textContent = 'Please enter a valid name!';
        messageSpan.style.color = '#e74c3c';
        return;
    }

    // Validate age is a number
    const ageNum = parseInt(age);
    if (isNaN(ageNum) || ageNum < 0) {
        messageSpan.textContent = 'Age must be a valid positive number!';
        messageSpan.style.color = '#e74c3c';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/insert_data`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                table_name: tableName,
                name: name,
                age: ageNum,
                username: currentRole
            })
        });

        const data = await response.json();

        if (!response.ok) {
            if (response.status === 404) {
                messageSpan.textContent = `Table '${tableName}' does not exist. Please create it first.`;
            } else {
                messageSpan.textContent = data.detail || 'Failed to insert data';
            }
            messageSpan.style.color = '#e74c3c';
            return;
        }

        // Clear the input fields
        document.getElementById('table-name-insert-data').value = '';
        document.getElementById('name').value = '';
        document.getElementById('age').value = '';

        messageSpan.textContent = `Data inserted into '${tableName}' successfully!`;
        messageSpan.style.color = '#27ae60';

        // Clear message after 3 seconds
        setTimeout(() => {
            messageSpan.textContent = '';
        }, 3000);
    } catch (error) {
        messageSpan.textContent = 'Error: ' + error.message;
        messageSpan.style.color = '#e74c3c';
    }
}

async function getAllTables() {
    if (currentRole !== 'role2') {
        displayResult('tables-result', 'Error: You need role2 permission');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/get_all_tables?username=${currentRole}`);
        const text = await response.text();
        if (!response.ok) {
            throw new Error(text);
        }
        
        const responseData = JSON.parse(text);
        displayResult('tables-result', formatTableData(responseData.tables));
    } catch (error) {
        displayResult('tables-result', 'Error: ' + error.message);
    }
}

async function getTableInfo() {
    const tableName = document.getElementById('table-name').value;
    if (currentRole !== 'role2') {
        displayResult('tables-result', 'Error: You need role2 permission');
        return;
    }
    
    
    // Check if table name is empty
    if (!tableName || tableName.trim() === '') {
        displayResult('tables-result', 'Please enter a table name!');
        return;
    }
    else{
        try {
            const response = await fetch(`${API_BASE_URL}/get_info_table?table_name=${tableName}&username=${currentRole}`);
            const text = await response.text();
            if (!response.ok) {
                throw new Error(text);
            }
            
            const responseData = JSON.parse(text);
            displayResult('tables-result', formatTableData(responseData.table_info));
            console.log(responseData.table_info);
        } catch (error) {
            displayResult('tables-result', 'Error: ' + error.message);
        }
    }
    
}

async function deleteTable() {
    if (currentRole !== 'role2') {
        displayResult('tables-result', 'Error: You need role2 permission');
        return;
    }
    
    const tableName = document.getElementById('table-name').value;
    if (!confirm(`Are you sure you want to delete table ${tableName}?`)) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/delete_table/${tableName}?username=${currentRole}`, {
            method: 'DELETE'
        });
        
        const text = await response.text();
        if (!response.ok) {
            throw new Error(text);
        }
        
        const responseData = JSON.parse(text);
        displayResult('tables-result', responseData.message);
    } catch (error) {
        displayResult('tables-result', 'Error: ' + error.message);
    }
}

async function updateTable() {
    if (currentRole !== 'role3') {
        displayResult('update-result', 'Error: You need role3 permission');
        return;
    }

    const tableName = document.getElementById('table-to-update').value;
    const newTableName = document.getElementById('new-table-name').value;
    const newNameCol = document.getElementById('new-name-col').value;
    const newAgeCol = document.getElementById('new-age-col').value;
    const messageSpan = document.getElementById('update-message');

    // Check if table name is empty
    if (!tableName || tableName.trim() === '') {
        messageSpan.textContent = 'Please enter a table name to update!';
        messageSpan.style.color = '#e74c3c';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/update_table`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                table_name: tableName,
                new_table_name: newTableName || null,
                new_name: newNameCol || null,
                new_age: newAgeCol ? parseInt(newAgeCol) : null,
                username: currentRole
            })
        });

        const data = await response.json();

        if (!response.ok) {
            messageSpan.textContent = data.detail || 'Failed to update table';
            messageSpan.style.color = '#e74c3c';
            return;
        }

        // Clear the input fields
        document.getElementById('table-to-update').value = '';
        document.getElementById('new-table-name').value = '';
        document.getElementById('new-name-col').value = '';
        document.getElementById('new-age-col').value = '';

        messageSpan.textContent = `Table ${tableName} updated successfully!`;
        messageSpan.style.color = '#27ae60';

        // Refresh the table list
        getAllTables();

        // Clear message after 3 seconds
        setTimeout(() => {
            messageSpan.textContent = '';
        }, 3000);
    } catch (error) {
        messageSpan.textContent = 'Error: ' + error.message;
        messageSpan.style.color = '#e74c3c';
    }
}

// Helper function to validate column names
function isValidColumnName(name) {
    // Column name must start with a letter and can only contain letters, numbers, and underscores
    return /^[a-zA-Z][a-zA-Z0-9_]*$/.test(name);
}

function displayResult(elementId, data) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (typeof data === 'string') {
        element.innerHTML = `<div class="message">${data}</div>`;
    } else {
        element.innerHTML = formatTableData(data);
    }
}

function formatTableData(data) {
    if (!data || (Array.isArray(data) && data.length === 0)) {
        return '<div class="message">No data found</div>';
    }
    
    if (Array.isArray(data)) {
        let html = '<table><thead><tr>';
        const headers = Object.keys(data[0]);
        headers.forEach(header => {
            html += `<th>${header}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        data.forEach(row => {
            html += '<tr>';
            headers.forEach(header => {
                html += `<td>${row[header]}</td>`;
            });
            html += '</tr>';
        });
        
        html += `</tbody></table>`;
        return html;
    }
    
    return `<pre>${JSON.stringify(data, null, 2)}</pre>`;
}
