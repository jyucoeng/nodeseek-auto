export default {
  async fetch(request, env, ctx) {
    return new Response("✅ NodeSeek 签到 Worker 正常运行中");
  },

  async scheduled(event, env, ctx) {
    await handleSignIn(env);
  }
}

async function handleSignIn(env) {
  const results = [];

  const wisdomStatements = [
    { text: "人生不是等待暴风雨过去，而是学会在雨中跳舞。", author: "维维安·格林" },
    { text: "我思故我在。", author: "笛卡尔" },
    { text: "你必须成为你希望这个世界出现的改变。", author: "甘地" },
    { text: "成功不是最终的，失败不是致命的，继续前进的勇气才是最重要的。", author: "丘吉尔" },
    { text: "真正的聪明，是知道自己无知。", author: "苏格拉底" },
    { text: "Stay hungry, stay foolish.", author: "乔布斯" },
    { text: "你若盛开，蝴蝶自来；你若精彩，天自安排。", author: "网络" },
    { text: "我们都有属于自己的时区，人生不必攀比。", author: "网络" },
    { text: "被讨厌的勇气，是自由的开端。", author: "岸见一郎" },
    { text: "给我一个支点，我可以撬动整个地球。", author: "阿基米德" }
  ];

  for (let i = 1; i <= 10; i++) {
    const cookie = env[`NS_COOKIE_${i}`];
    const user = env[`USER_${i}`];
    const tgToken = env.TG_BOT_TOKEN;
    const tgUser = env.TG_USER_ID;

    if (!cookie || !user) continue;

    const url = "https://node.seek.ink/plugin.php?id=dsu_paulsign:sign&operation=qiandao&formhash=xxxx";

    try {
      const res = await fetch(url, {
        method: "GET",
        headers: {
          "Cookie": cookie,
          "User-Agent": "Mozilla/5.0"
        }
      });

      const text = await res.text();
      const wisdom = getRandomWisdom(wisdomStatements);
      let msg = "";

      if (text.includes("签到成功")) {
        msg = `✅ NodeSeek 签到成功\n\n` +
              `账号 *${user}*：今天已完成签到。\n\n` +
              `💡 出自 *${wisdom.author}*：${wisdom.text}`;
      } else {
        const reason = extractFailureReason(text);
        msg = `❌ NodeSeek 签到失败\n\n` +
              `账号 *${user}*：${reason}\n\n` +
              `💡 出自 *${wisdom.author}*：${wisdom.text}`;
      }

      await sendTG(tgToken, tgUser, msg);
      results.push(msg);
    } catch (err) {
      const msg = `❌ *${user}* 签到异常：${err.message}`;
      await sendTG(env.TG_BOT_TOKEN, env.TG_USER_ID, msg);
      results.push(msg);
    }
  }

  return results;
}

async function sendTG(botToken, chatId, msg) {
  if (!botToken || !chatId) return;
  const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text: msg,
      parse_mode: "Markdown"
    })
  });
}

function extractFailureReason(text) {
  if (text.includes("您今日已经签过到")) {
    return "已签到过，请勿重复操作。";
  } else if (text.includes("账号或密码错误")) {
    return "账号或密码错误，请检查登录信息。";
  } else if (text.includes("未登录") || text.includes("Cookie无效")) {
    return "未登录或 Cookie 无效，请检查 Cookie 设置。";
  }

  const match = text.match(/<div[^>]*class=["']?alert_error["']?[^>]*>([\s\S]*?)<\/div>/i) ||
                text.match(/<p[^>]*class=["']?error["']?[^>]*>([\s\S]*?)<\/p>/i) ||
                text.match(/<div[^>]*id=["']?messagetext["']?[^>]*>[\s\S]*?<p>(.*?)<\/p>/i);

  if (match && match[1]) {
    const raw = match[1].replace(/<[^>]+>/g, '').trim();
    return raw || "发生未知错误，请稍后再试。";
  }

  return "未知错误，请稍后再试。";
}

function getRandomWisdom(list) {
  return list[Math.floor(Math.random() * list.length)];
}
