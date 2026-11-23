// Answers every request with the inbox's UIDVALIDITY and UIDNEXT, which only
// change when mail arrives. STATUS reads them without selecting the mailbox.
import { createServer } from 'node:http';
import { createRequire } from 'node:module';

const { ImapFlow } = createRequire('/app/package.json')('imapflow');
const { IMAP_HOST: host, IMAP_USER: user, IMAP_PASSWORD: pass } = process.env;

createServer(async (req, res) => {
  // Hermes gives up on the request after 30 seconds.
  const client = new ImapFlow({
    host, port: 993, secure: true, auth: { user, pass }, logger: false,
    connectionTimeout: 10_000, greetingTimeout: 10_000, socketTimeout: 20_000,
  });
  client.on('error', () => {});
  try {
    await client.connect();
    // false, not an exception, when the server refuses STATUS.
    const status = await client.status('INBOX', { uidValidity: true, uidNext: true });
    if (!status) throw new Error('STATUS failed');
    res.end(`uidvalidity=${status.uidValidity} uidnext=${status.uidNext}\n`);
  } catch {
    res.writeHead(502).end();
  } finally {
    await client.logout().catch(() => client.close());
  }
}).listen(8080);
