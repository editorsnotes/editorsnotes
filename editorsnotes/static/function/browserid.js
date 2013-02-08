;

(function () {
  var logoutURL = null
    , loginFailed = location.search.indexOf('bid_login_failed=1') !== -1
  ;

  $(document).on('click', '.browserid-login', function (e) {
    var $loginButton = $(this)
    ;
    e.preventDefault();
    navigator.id.request({
      'siteName': "Editorsʼ Notes" // apostrophe is blocked, this is u02bc
    });
  });

  $(document).on('click', '.browserid-logout', function (e) {
    e.preventDefault();
    logoutURL = this.href;
    navigator.id.logout();
  });

  navigator.id.watch({
    loggedInUser: EditorsNotes.loggedInUser,

    onlogin: function (assertion) {
      if (loginFailed) {
        // No account for this email, logout from this browserid
        navigator.id.logout();
        return;
      }
      if (assertion) {
        var $assertion = $('#id_assertion');
        $assertion.val(assertion.toString());
        $assertion.parent('form').submit();
      }
    },

    onlogout: function () {
      if (loginFailed) {
        // Redirect back to login page with alert that no account was connected
        // to the given email.
        window.location.replace('/accounts/login/?bad_email=1');
      } else if (logoutURL) {
        window.location = logoutURL;
      }
    }

  });

})();
