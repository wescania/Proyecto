import requests
from bs4 import BeautifulSoup

# Palabras clave para detectar librerías
LIBRERIAS_CONOCIDAS = [
    'jquery', 'react', 'vue', 'bootstrap', 'axios', 'lodash', 'moment',
    'angular', 'ember', 'backbone', 'd3', 'chartjs', 'three', 'popper',
    'rxjs', 'underscore', 'semantic', 'materialize', 'animejs', 'gsap',
    'handlebars', 'mustache', 'knockout', 'zepto', 'babel', 'core-js',
    'redux', 'mobx', 'next', 'nuxt', 'svelte', 'preact', 'vuex', 'vuetify',
    'tailwind', 'bulma', 'foundation', 'uikit', 'swiper', 'slick', 'datatables',
    'sweetalert', 'toastr', 'noty', 'select2', 'dropzone', 'fullcalendar',
    'leaflet', 'openlayers', 'videojs', 'plyr', 'pdfjs', 'socket.io', 'pusher',
    'highcharts', 'echarts', 'amcharts', 'apexcharts', 'c3', 'chartist',
    'zxcvbn', 'crypto-js', 'mathjs', 'date-fns', 'luxon', 'dayjs',
    'validator', 'js-cookie', 'uuid', 'qrcode', 'jszip', 'xlsx', 'handsontable',
    'ag-grid', 'tabulator', 'sortablejs', 'interactjs', 'dragula', 'tippy',
    'shepherd', 'introjs', 'shepherdjs', 'clipboard', 'clipboardjs', 'filepond',
    'parsley', 'formvalidation', 'validatejs', 'just-validate', 'yup',
    'formik', 'vee-validate', 'vuelidate', 'alpinejs', 'stimulus', 'htmx',
    'livewire', 'inertia', 'turbolinks', 'barba', 'anime', 'velocity',
    'scrollmagic', 'locomotive-scroll', 'smooth-scroll', 'scrollreveal',
    'wowjs', 'aos', 'lottie', 'particlesjs', 'typed', 'typeit', 'glidejs',
    'splide', 'flickity', 'photoswipe', 'lightgallery', 'fancybox', 'magnific-popup',
    'colorbox', 'baguettebox', 'viewerjs', 'cropper', 'croppie', 'pica',
    'fabric', 'konva', 'paperjs', 'pixi', 'phaser', 'babylonjs', 'threejs',
    'zdog', 'svg.js', 'canvg', 'raphael', 'jointjs', 'mermaid', 'gojs',
    'mxgraph', 'cytoscape', 'vis', 'sigma', 'dhtmlx', 'webix', 'extjs',
    'sencha', 'qooxdoo', 'enyo', 'dojo', 'yui', 'prototype', 'mootools',
    'scriptaculous', 'requirejs', 'systemjs', 'jspm', 'webpack', 'rollup',
    'parcel', 'browserify', 'grunt', 'gulp', 'bower', 'npm', 'yarn',
    'pnpm', 'esbuild', 'vite', 'snowpack', 'astro', 'eleventy', 'hexo',
    'gatsby', 'gridsome', 'hugo', 'jekyll', 'nextjs', 'nuxtjs', 'sapper',
    'sveltekit', 'remix', 'blitz', 'redwood', 'quasar', 'ionic', 'cordova',
    'capacitor', 'electron', 'nwjs', 'tauri', 'react-native', 'expo',
    'native-script', 'flutter', 'unity', 'unreal', 'godot', 'photon',
    'playcanvas', 'babylon', 'aframe', 'three', 'p5', 'processing',
    'createjs', 'easeljs', 'tweenjs', 'soundjs', 'preloadjs', 'zlib',
    'lz-string', 'pako', 'brotli', 'fflate', 'compressjs', 'crypto',
    'sjcl', 'forge', 'openpgp', 'tweetnacl', 'bcrypt', 'argon2',
    'scrypt', 'pbkdf2', 'jwt', 'jsonwebtoken', 'jose', 'passport',
    'auth0', 'firebase', 'amplify', 'aws-sdk', 'azure', 'gapi', 'okta',
    'keycloak', 'stormpath', 'cognito', 'msal', 'adal', 'oidc-client',
    'openid', 'oauth', 'oauth2', 'openid-client', 'openidconnect',
    'openidconnectjs', 'openidconnect-client', 'openidconnect-clientjs',
    'openidconnect-client-js', 'openidconnect-client-js-sdk', 'openidconnect-client-js-sdk-core',
    'openidconnect-client-js-sdk-core-js', 'openidconnect-client-js-sdk-core-js-core',
    'openidconnect-client-js-sdk-core-js-core-js', 'openidconnect-client-js-sdk-core-js-core-js-core',
    'openidconnect-client-js-sdk-core-js-core-js-core-js', 'openidconnect-client-js-sdk-core-js-core-js-core-js-core',
    'openidconnect-client-js-sdk-core-js-core-js-core-js-core-js', 'openidconnect-client-js-sdk-core-js-core-js-core-js-core-js-core',
    'openidconnect-client-js-sdk-core-js-core-js-core-js-core-js-core-js', 'openidconnect-client-js-sdk-core-js-core-js-core-js-core-js-core-js-core',
    'openidconnect-client-js-sdk-core-js-core-js-core-js-core-js-core-js-core-js', 'openidconnect-client-js-sdk-core-js-core-js-core-js-core-js-core-js-core-js-core',
    'openidconnect-client-js-sdk-core-js-core-js-core-js-core-js-core-js-core-js-core-js', 'openidconnect-client-js-sdk-core-js-core-js-core-js-core-js-core-js-core-js-core-js-core',
    'openidconnect-client-js-sdk-core-js-core-js-core-js-core-js-core-js-core-js-core-js-core-js',
]

def extraer_librerias_js(url):
    try:
        #simulamos ser un navegador para evitar bloqueos por parte del servidor
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers, timeout=10)
        # Si la respuesta no es 200, devolvemos mensaje bonito
        if response.status_code != 200:
            return [], f"❌ No se puede analizar esta URL.\nCódigo HTTP: {response.status_code} - {response.reason}"
        html = response.text
    except requests.exceptions.Timeout:
        return [], "⏱️ No se pudo analizar la URL porque tardó demasiado en responder (timeout)."

    except requests.exceptions.TooManyRedirects:
        return [], "🔁 No se pudo analizar la URL porque redirige demasiadas veces."

    except requests.exceptions.RequestException as e:
        return [], "🚫 No se pudo analizar la URL por un error de conexión o acceso."

    except Exception as e:
        return [], "⚠️ Ocurrió un error inesperado al analizar la URL."

    # Analizar el HTML para buscar <script src=...>
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script', src=True)

    librerias_detectadas = set()
    for script in scripts:
        src = script['src'].lower()
        for lib in LIBRERIAS_CONOCIDAS:
            if lib in src:
                librerias_detectadas.add(lib)

    return list(librerias_detectadas), None
