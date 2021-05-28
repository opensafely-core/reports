from django.contrib.auth.forms import AuthenticationForm


class ReportsAuthenticationForm(AuthenticationForm):
    """Custom AuthenticationForm to override styling"""

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "autocomplete": "username",
                "spellcheck": "false",
                "autocorrect": "false",
                "autocapitalize": "none",
                "class": "appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "autocomplete": "current-password",
                "spellcheck": "false",
                "autocorrect": "false",
                "class": "appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm",
            }
        )
