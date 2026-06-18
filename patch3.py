with open("reports/templates/reports/report_detail.html", "r") as f:
    content = f.read()

chat_html = """      </div>
    </div>

    <!-- Internal Discussion Chat Block -->
    <div class="card shadow-sm border-0 mt-3">
      <div class="card-body">
        <h2 class="h6 mb-3">Internal Discussion</h2>
        
        <!-- Chat History -->
        <div class="mb-3" style="max-height: 300px; overflow-y: auto;">
          {% if report.comments.all %}
            {% for comment in report.comments.all %}
              <div class="mb-3 p-2 rounded {% if comment.author == request.user %}bg-primary-subtle border border-primary-subtle text-end ms-auto{% else %}bg-light border text-start me-auto{% endif %}" style="max-width: 85%;">
                <div class="d-flex justify-content-between align-items-center mb-1 {% if comment.author == request.user %}flex-row-reverse{% endif %}">
                  <span class="fw-bold small text-body-secondary">{{ comment.author.profile.role }} | {{ comment.author.get_full_name|default:comment.author.username }}</span>
                  <span class="text-body-tertiary" style="font-size: 0.75rem;">{{ comment.created_at|date:"M d, H:i" }}</span>
                </div>
                <div class="text-dark" style="white-space: pre-wrap; font-size: 0.9rem;">{{ comment.message }}</div>
              </div>
            {% endfor %}
          {% else %}
            <div class="text-muted small">No comments yet. Start the discussion below.</div>
          {% endif %}
        </div>

        <!-- Chat Input -->
        <form method="post" action="{% url 'reports:add_case_comment' report.pk %}">
          {% csrf_token %}
          <div class="input-group">
            {{ comment_form.message }}
            <button class="btn btn-primary" type="submit">Send</button>
          </div>
        </form>
        
      </div>
    </div>
    <!-- End Chat Block -->
"""

content = content.replace("      </div>\n    </div>\n\n  </div>", chat_html + "\n  </div>")

with open("reports/templates/reports/report_detail.html", "w") as f:
    f.write(content)
