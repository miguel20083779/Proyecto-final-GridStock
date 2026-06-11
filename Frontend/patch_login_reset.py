from pathlib import Path

path = Path('frontend/login.html')
text = path.read_text(encoding='utf-8')
text = text.replace('\r\n', '\n')
needle = """                } catch (error) {
                    showAlert('Error de conexión', 'error');
                }
            });
    </script>
</body>
</html>
"""
insert = """                } catch (error) {
                    showAlert('Error de conexión', 'error');
                }
            });

            // Reset Password
            document.getElementById('reset-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('reset-username').value;
                const password = document.getElementById('reset-password').value;
                const confirmPassword = document.getElementById('reset-confirm').value;

                if (password !== confirmPassword) {
                    showAlert('Las contraseñas no coinciden.', 'error');
                    return;
                }
                if (password.length < 4) {
                    showAlert('La contraseña debe tener al menos 4 caracteres.', 'error');
                    return;
                }

                try {
                    const response = await fetch(`${API_URL}/auth/reset-password`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password })
                    });

                    const data = await response.json();
                    if (data.success) {
                        showAlert(data.message + ' Ahora puedes iniciar sesión.', 'success');
                        setTimeout(showLogin, 1500);
                    } else {
                        showAlert(data.message, 'error');
                    }
                } catch (error) {
                    showAlert('Error de conexión', 'error');
                }
            });
    </script>
</body>
</html>
"""

if needle not in text:
    raise RuntimeError('Needle not found in login.html')
text = text.replace(needle, insert)
path.write_text(text, encoding='utf-8')
print('updated')
