def get_html_template(success: bool) -> str:
    if success:
        color = "color: #c2f970"
        header = "Authentication successful"
        detail = "You can close this tab"
    else:
        color = "color: #e94949"
        header = "Authentication failed"
        detail = "Message snwflake on discord :("

    return f"""
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="robots" content="noindex, nofollow" />
<style>
html,
body {{height: 100%;background-color: #2a2a2a;}}
body {{margin: 0;}}
p {{padding: 5px;margin: 10px;font-weight: bold;text-align: center;font-family: gill sans, sans-serif;}}
.container {{height: 100%;display: flex;align-items: center;justify-content: center;{color}}}
.header {{font-size: 3em;text-decoration: underline;}}
</style>
</head>
<body>
<div class="container">
<div>
<p class="header">{header}</p>
<p class="detail">{detail}</p>
</div>
</div>
</body>
    """

