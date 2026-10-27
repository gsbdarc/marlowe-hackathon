# frozen_string_literal: true

# Bridge jekyll-last-modified-at to just-the-docs.
#
# The plugin sets `page.last_modified_at`; just-the-docs 0.12.0's footer reads
# `page.last_modified_date` (_includes/components/footer.html). The names differ,
# so enabling the plugin and `last_edit_timestamp` alone renders nothing at all —
# and silently, because the theme just skips the block when the value is missing.
#
# Copy the Time across and let the theme format it with `last_edit_time_format`,
# keeping the date format configurable in _config.yml rather than hard-coded here.
#
# Runs on site :post_read rather than per-item :post_init deliberately: at
# :post_init this competes with the gem's own hook on the same event, and the
# ordering is not something to rely on. By :post_read every page has been read
# and its determinator attached.
Jekyll::Hooks.register(:site, :post_read) do |site|
  (site.pages + site.documents).each do |item|
    determinator = item.data["last_modified_at"]
    next unless determinator.respond_to?(:last_modified_at_time)

    begin
      item.data["last_modified_date"] = determinator.last_modified_at_time
    rescue Errno::ENOENT
      # Generated pages have no file on disk. Leave the key unset; the theme
      # then omits the line rather than failing the build.
      next
    end
  end
end
