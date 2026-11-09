-- Two-column acmart cannot use pandoc's longtable: render every table as a tabularx inside table / table*.
local function cell_text(cell)
  return (pandoc.write(pandoc.Pandoc(cell), "latex"):gsub("\n$", ""))
end
function Table(tbl)
  local t = pandoc.utils.to_simple_table(tbl)
  local ncol = #t.headers
  local wide = ncol > 3
  local env = wide and "table*" or "table"
  local width = wide and "\\textwidth" or "\\columnwidth"
  -- columns whose cells are all short get a fixed centred column; the rest share the remaining width
  local spec = "l"
  for j = 2, ncol do
    local short = #pandoc.utils.stringify(t.headers[j]) <= 8
    for _, row in ipairs(t.rows) do if #pandoc.utils.stringify(row[j]) > 8 then short = false end end
    spec = spec .. (short and "c" or "X")
  end
  local out = { "\\begin{" .. env .. "}[t]\\small\\centering" }
  local cap = (pandoc.write(pandoc.Pandoc({ pandoc.Plain(t.caption) }), "latex"):gsub("\n$", ""))
  if cap ~= "" then table.insert(out, "\\caption{" .. cap .. "}") end
  table.insert(out, "\\begin{tabularx}{" .. width .. "}{" .. spec .. "}\\toprule")
  local hdr = {}
  for _, c in ipairs(t.headers) do table.insert(hdr, "\\textbf{" .. cell_text(c) .. "}") end
  table.insert(out, table.concat(hdr, " & ") .. " \\\\ \\midrule")
  for _, row in ipairs(t.rows) do
    local cells = {}
    for _, c in ipairs(row) do table.insert(cells, cell_text(c)) end
    table.insert(out, table.concat(cells, " & ") .. " \\\\")
  end
  table.insert(out, "\\bottomrule\\end{tabularx}\\end{" .. env .. "}")
  return pandoc.RawBlock("latex", table.concat(out, "\n"))
end
