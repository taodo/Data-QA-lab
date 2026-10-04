import {defineConfig} from 'vite';
export default defineConfig({server:{proxy:{'/api':'http://127.0.0.1:8000'}},build:{rollupOptions:{output:{manualChunks(id){if(/node_modules.*(codemirror|lezer)/.test(id))return 'editor';if(id.includes('node_modules'))return 'vendor';}}}}});
