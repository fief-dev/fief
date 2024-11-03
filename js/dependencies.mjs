import htmx from 'htmx.org'
import _hyperscript from 'hyperscript.org'
import slugify from 'slugify'

window.htmx = htmx
_hyperscript.browserInit();
window.slugify = slugify
