"""${messages | truncate(46, True)}..."""
<%- set callable = '  '.join([x[0] for x in context.get_current_parameters()]) %>
<%- set msg = messages[0] %>
<%- set (p, filename, line) = msg %>

# ${p.name}:
# ${filename}:${line}

from alembic import op
import sqlalchemy as sa

${imports if imports else ""}

# ${callable}
def ${p.name}():
${messages | indent(4, False)}
