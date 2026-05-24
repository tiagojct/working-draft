-- fmup.lua
--
-- Two jobs:
--
-- 1. Forward `fmup.logo` metadata to the format-specific keys that
--    Quarto / Reveal consume (revealjs `logo`, website / book navbar
--    `logo`). Users supply the path once and it lands everywhere.
--
-- 2. Emit Open Graph + Twitter Card <meta> tags for HTML / Reveal
--    output, populated from each page's frontmatter (title,
--    description, lang, author). Done in Lua because Quarto's
--    `include-in-header` does not interpolate Pandoc template
--    variables, so the equivalent static partial would emit raw
--    `$if(title)$` placeholders.
--
-- The filter is intentionally conservative: existing user-set values
-- are NEVER overwritten, and meta-tag emission is skipped for any
-- field the user did not declare.

local function get_fmup_logo(meta)
  if meta.fmup == nil then return nil end
  if type(meta.fmup) == 'table' and meta.fmup.logo ~= nil then
    return meta.fmup.logo
  end
  return nil
end

local function forward_logo(meta, logo)
  if meta.logo == nil then
    meta.logo = logo
  end

  if meta.website ~= nil and type(meta.website) == 'table' then
    if meta.website.navbar == nil then
      meta.website.navbar = pandoc.MetaMap({})
    end
    if type(meta.website.navbar) == 'table' and meta.website.navbar.logo == nil then
      meta.website.navbar.logo = logo
    end
  end

  if meta.book ~= nil and type(meta.book) == 'table' then
    if meta.book.navbar == nil then
      meta.book.navbar = pandoc.MetaMap({})
    end
    if type(meta.book.navbar) == 'table' and meta.book.navbar.logo == nil then
      meta.book.navbar.logo = logo
    end
  end
end

-- Render a Pandoc Inlines / MetaInlines value back to a plain string
-- suitable for an HTML attribute. Falls back to "" when the value is
-- absent so the caller's nil-check still works (we just refuse to
-- emit attribute = "" tags).
local function meta_to_string(value)
  if value == nil then return nil end
  local s = pandoc.utils.stringify(value)
  if s == nil or s == "" then return nil end
  -- Strip HTML reserved chars so the attribute stays well-formed
  -- when titles contain ampersands or quotes.
  s = s:gsub('&', '&amp;'):gsub('"', '&quot;'):gsub('<', '&lt;'):gsub('>', '&gt;')
  return s
end

-- Extract a comma-joined author string from Pandoc's structured author
-- metadata. Pandoc accepts either a single string or a list of
-- {name = ..., affiliation = ...} maps; handle both.
local function authors_string(meta)
  if meta.author == nil then return nil end
  local parts = {}
  local a = meta.author
  if a.t == 'MetaList' or (type(a) == 'table' and a[1] ~= nil) then
    for _, entry in ipairs(a) do
      if type(entry) == 'table' and entry.name ~= nil then
        table.insert(parts, pandoc.utils.stringify(entry.name))
      else
        table.insert(parts, pandoc.utils.stringify(entry))
      end
    end
  else
    table.insert(parts, pandoc.utils.stringify(a))
  end
  if #parts == 0 then return nil end
  return table.concat(parts, ", ")
end

-- Resolve an OG image URL from the metadata. Looks at, in order:
--   1. `meta.fmup.og-image` (extension-specific; one place to set
--      institutional default for the whole project)
--   2. `meta.website.open-graph.image` (Quarto's standard channel,
--      respected if the project already declares it)
--   3. `meta["og-image"]` (per-page override)
-- Returns nil if none set; absence of og:image is acceptable per
-- protocol (Facebook / Twitter just fall back to no preview image).
local function get_og_image(meta)
  if meta.fmup ~= nil and type(meta.fmup) == 'table' and meta.fmup['og-image'] ~= nil then
    return meta_to_string(meta.fmup['og-image'])
  end
  if meta.website ~= nil and type(meta.website) == 'table'
     and meta.website['open-graph'] ~= nil
     and type(meta.website['open-graph']) == 'table'
     and meta.website['open-graph'].image ~= nil then
    return meta_to_string(meta.website['open-graph'].image)
  end
  if meta['og-image'] ~= nil then
    return meta_to_string(meta['og-image'])
  end
  return nil
end

local function emit_social_meta(meta)
  -- Only run inside HTML-ish outputs where <meta> tags belong.
  if not (quarto.doc.is_format("html") or quarto.doc.is_format("revealjs")) then
    return
  end

  local title       = meta_to_string(meta.title)
  local description = meta_to_string(meta.description)
  local lang        = meta_to_string(meta.lang)
  local author      = authors_string(meta)
  local og_image    = get_og_image(meta)

  local lines = {}

  if title       then table.insert(lines, '<meta property="og:title" content="'       .. title       .. '">') end
  if description then table.insert(lines, '<meta property="og:description" content="' .. description .. '">') end
  table.insert(lines, '<meta property="og:type" content="article">')
  if lang        then table.insert(lines, '<meta property="og:locale" content="'      .. lang        .. '">') end
  if author      then
    -- Escape author the same way as the other attributes.
    local safe_author = author:gsub('&', '&amp;'):gsub('"', '&quot;')
    table.insert(lines, '<meta property="article:author" content="' .. safe_author .. '">')
  end
  if og_image    then table.insert(lines, '<meta property="og:image" content="'       .. og_image    .. '">') end

  -- Twitter Card: summary_large_image when we have an image, plain
  -- summary otherwise. Crawlers downgrade automatically if asked to
  -- preview a card type and no image is supplied, but the cleaner
  -- signal here is to pick the right card up front.
  if og_image then
    table.insert(lines, '<meta name="twitter:card" content="summary_large_image">')
    table.insert(lines, '<meta name="twitter:image" content="' .. og_image .. '">')
  else
    table.insert(lines, '<meta name="twitter:card" content="summary">')
  end
  if title       then table.insert(lines, '<meta name="twitter:title" content="'       .. title       .. '">') end
  if description then table.insert(lines, '<meta name="twitter:description" content="' .. description .. '">') end

  quarto.doc.include_text('in-header', table.concat(lines, "\n"))
end

function Meta(meta)
  local logo = get_fmup_logo(meta)
  if logo ~= nil then
    forward_logo(meta, logo)
  end

  emit_social_meta(meta)

  return meta
end
