from __future__ import annotations
from .doctor import status

def capabilities():
    s=status()
    return {
      'core': {
        'ready': s['core_ready'],
        'commands': ['doctor','capabilities','profiles','init','inspect','context','scaffold','replace','validate','render','evidence list'],
        'api_key_required': False
      },
      'advanced_word': {
        'backend': 'docx-mcp-server',
        'available': s['docx-mcp-server'],
        'features': ['tracked_changes','comments','footnotes','endnotes','bookmarks','fields','cross_references','charts','equations','content_controls','advanced_tables','protection','structural_ooxml_audit'],
        'policy': 'Expose through an adapter/agent only when needed; do not preload hundreds of tools.'
      }
    }
