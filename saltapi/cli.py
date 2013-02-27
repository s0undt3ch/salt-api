'''
CLI entry-point for salt-api
'''
# Import python libs
import os
import sys
import getpass

# Import salt libs
from salt.utils.verify import verify_env, verify_files
from salt.utils.parsers import (
    ConfigDirMixIn,
    DaemonMixIn,
    LogLevelMixIn,
    MergeConfigMixIn,
    OptionParser,
    OptionParserMeta,
    PidfileMixin
)

# Import salt-api libs
import saltapi.client
import saltapi.config
import saltapi.version


class SaltAPI(OptionParser, ConfigDirMixIn, LogLevelMixIn, PidfileMixin,
              DaemonMixIn, MergeConfigMixIn):
    '''
    The cli parser object used to fire up the salt api system.
    '''
    __metaclass__ = OptionParserMeta

    VERSION = saltapi.version.__version__

    # ConfigDirMixIn config filename attribute
    _config_filename_ = 'master'

    # LogLevelMixIn default log level attribute
    _default_logging_level_ = 'info'

    def _mixin_after_parsed(self):
        # Remove log_level_logfile from config if set to None so it can be
        # equal to console log_level
        if self.config['log_level_logfile'] is None:
            self.config.pop('log_level_logfile')

    def setup_config(self):
        return saltapi.config.api_config(self.get_config_file_path())

    def run(self):
        '''
        Run the api
        '''
        self.parse_args()

        try:
            if self.config['verify_env']:
                verify_env(
                    [os.path.dirname(self.config['conf_file'])],
                    getpass.getuser()
                )
                logfile = self.config['log_file']
                if logfile is not None and (
                        not logfile.startswith('tcp://') or
                        not logfile.startswith('udp://') or
                        not logfile.startswith('file://')):
                    # Logfile is not using Syslog, verify
                    verify_files([logfile], getpass.getuser())
        except OSError as err:
            sys.exit(err.errno)

        # Setup log file logging
        self.setup_logfile_logger()

        self.daemonize_if_required()
        self.set_pidfile()

        client = saltapi.client.SaltAPIClient(self.config)
        client.run()
