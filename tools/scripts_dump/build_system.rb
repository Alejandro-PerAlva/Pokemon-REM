# Uso: ruby tools/scripts_dump/build_system.rb   (desde la raíz del proyecto; antes: python3 tools/rebalance/phase1/build_event_architecture.py)
# Amplía @variables (251) y @switches (831) de Data/System.rxdata con los nombres de tools/rebalance/phase1/event_arch.json.
# Idempotente: respeta los nombres existentes salvo los que el JSON define; guarda backup Data/System.rxdata.bak_pre_events una vez.
require 'json'
module RPG
  class System; class Words; end; class TestBattler; end; end
  class AudioFile; end
end
class Table; def self._load(s); o=new; o.instance_variable_set(:@raw,s); o; end; def _dump(l=-1); @raw; end; end
class Color; def self._load(s); o=new; o.instance_variable_set(:@raw,s); o; end; def _dump(l=-1); @raw; end; end
class Tone;  def self._load(s); o=new; o.instance_variable_set(:@raw,s); o; end; def _dump(l=-1); @raw; end; end
f='Data/System.rxdata'; bak=f+'.bak_pre_events'
File.binwrite(bak,File.binread(f)) if !File.exist?(bak)
arch=JSON.parse(File.read('tools/rebalance/phase1/event_arch.json',:encoding=>'UTF-8'))
sys=Marshal.load(File.binread(bak))
vars=sys.instance_variable_get(:@variables); sws=sys.instance_variable_get(:@switches)
vars.fill('',vars.size...arch['var_len']); sws.fill('',sws.size...arch['switch_len'])
arch['vars'].each{|i,n| vars[i.to_i]=n.dup.force_encoding('UTF-8')}
arch['switches'].each{|i,n| i=i.to_i; raise "switch #{i} ocupado: #{sws[i]}" if sws[i] && !sws[i].empty? && sws[i]!=n; sws[i]=n.dup.force_encoding('UTF-8')}
sws[400]='REM_PIA_QUESTS_SWITCH'
{135=>'Boss_Fight_Doble',287=>'Wonder_Trade_Usado'}.each{|i,n| sws[i]=n if sws[i].nil? || sws[i].empty?}
raise 'var 50' if vars[50]!='Tope_Nivel_Actual'
File.binwrite(f,Marshal.dump(sys))
puts "System.rxdata OK: variables=#{vars.size-1} switches=#{sws.size-1}"
