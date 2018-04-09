import request

from disco.bot import Plugin

class FunPlugin(Plugin):
  @Plugin.command('badjoke')
  def badjoke(self, event):
    for _ in range 