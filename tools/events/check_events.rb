# Uso: ruby tools/events/check_events.rb PREFIJO_ MAPA [MAPA...]  -> compila (sintaxis Ruby) todos los scripts de los eventos con ese prefijo.
load "tools/mocks.rb"
bad=0; tot=0
prefix=ARGV[0]||"ALBOR_"
ARGV[1..-1].map{|x| x.to_i}.each{|id|
  m=Marshal.load(File.binread(format("Data/Map%03d.rxdata",id))); ev=iv(m,:events)
  ev.each{|k,e| next unless iv(e,:name).to_s.start_with?(prefix)
    iv(e,:pages).each{|pg| s=nil
      iv(pg,:list).each{|c| code=iv(c,:code); pr=iv(c,:parameters)
        if code==355 then s=pr[0].dup elsif code==655 && s then s<<"\n"<<pr[0] else
          (begin; RubyVM::InstructionSequence.compile(s.dup.force_encoding('UTF-8')); tot+=1; rescue SyntaxError=>x; bad+=1; puts "SYNTAX #{id} #{iv(e,:name)}: #{x.message[0,200]}"; end) if s; s=nil
          if code==111 && pr[0]==12 then (begin; RubyVM::InstructionSequence.compile(pr[1].dup.force_encoding('UTF-8')); tot+=1; rescue SyntaxError=>x; bad+=1; puts "SYNTAX cond #{pr[1]}"; end) end
        end }
    }}
  puts "Map#{id}: #{ev.size} eventos totales, w/h #{iv(m,:width)}x#{iv(m,:height)}"
}
puts "scripts compilados=#{tot} errores=#{bad}"
