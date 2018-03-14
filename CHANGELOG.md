# Change Log

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - unreleased

## [1.4.1] - 2018-03-13
### Fixed
- Rejected domain edits due to missing CSRF token.

## [1.4.0] - 2018-03-13

### Added
- Ability to modify the SOA's main nameserver and contact (MNAME and RNAME, respectively).

## [1.3.3] - 2016-11-26
### Fixed
- MX records now get a default prio=0 if not set

## [1.3.2] - 2016-11-20
### Added
- Ability to delete DynDNS keys

## [1.3.1] - 2016-11-19
### Added
- Ability to set the TSIG algorithm (previously everything was hmac-sha256)

## [1.3.0] - 2016-11-19
### Added
- Add TSIG keys to domains
- Autocreates NSEC3 params for new domains

### Fixed
- View skips records without type ([#4](https://github.com/thusoy/poff/issues/4))

## [1.2.0] - 2015-11-15
### Added
- Allow modifying existing records ([#1](https://github.com/thusoy/poff/issues/1))
- No-mail SPF record is added by default for new domains ([#6](https://github.com/thusoy/poff/issues/6))

## [1.1.2] - 2015-05-24
### Added
- Change log

### Changed
- Show DynDNS options only for A and AAAA records
- Records under the same subdomain are now grouped together in the UI
- Long values (like DNSSEC/DKIM-keys) are now truncated to not distort the UI

## [1.1.1] - 2015-02-18
### Fixed
- Domains on front page is now sorted consistently

### Added
- Can now handle IPv6-tunneled DynDNS updates of IPv4 records

## [1.1.0] - 2014-09-06
### Added
- Possibility to re-key DynDNS records

## [1.0.1] - 2014-09-06
### Fixed
- Python 3 compatibility

## [1.0.0] - 2014-09-06
### Note
First release.

[unreleased]: https://github.com/thusoy/poff/compare/v1.4.1...HEAD
[1.4.1]: https://github.com/thusoy/poff/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/thusoy/poff/compare/v1.3.3...v1.4.0
[1.3.3]: https://github.com/thusoy/poff/compare/v1.3.2...v1.3.3
[1.3.2]: https://github.com/thusoy/poff/compare/v1.3.1...v1.3.2
[1.3.1]: https://github.com/thusoy/poff/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/thusoy/poff/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/thusoy/poff/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/thusoy/poff/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/thusoy/poff/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/thusoy/poff/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/thusoy/poff/compare/v1.0.0...v1.0.1
