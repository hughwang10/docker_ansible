$(function() {

 $('#jstree').jstree({core : {
    'data' : server_list
 }});

  $('#jstree_b').on('load_node.jstree', function (e, data) {
    ids = data.node.children_d;
    $('#jstree_b').jstree(true).load_all();
  });


  $('#jstree_b').jstree({core : {
     'data' : problems
  }});


  $('#jstree_c').jstree({core : {
    'data' : network_problems
  }});

  $('a.toDashboard').click(function (e) {
    e.preventDefault();
    var url = location.href;
    $('#myTabs a[href="#dashboard"]').tab('show')
    location.href = '#';
    history.replaceState(null,null,url);
  });

  var $lightbox = $('#lightbox');

  $('[data-target="#lightbox"]').on('click', function(event) {
      var $img = $(this).find('img'), 
      src = $img.attr('src'),
      alt = $img.attr('alt'),
      css = {
      'maxWidth': $(window).width() - 100,
      'maxHeight': $(window).height() - 100
      };

      $lightbox.find('.close').addClass('hidden');
      $lightbox.find('img').attr('src', src);
      $lightbox.find('img').attr('alt', alt);
      $lightbox.find('img').css(css);
    });

  $lightbox.on('shown.bs.modal', function (e) {
      var $img = $lightbox.find('img');

      $lightbox.find('.modal-dialog').css({'width': $img.width()});
      $lightbox.find('.close').removeClass('hidden');
    });

});

var ids = []; 

function findIds(server) {
  var out = [];
  
  for (var x=0;x<ids.length;x++){
    if (ids[x].split('_')[0] == server){
      out.push(ids[x]);
    }
  }
  return out;
}

function highlightNode(server) {
  var idds = findIds(server);

  $('#jstree_b').jstree(true).deselect_all();
  $('#jstree_b').jstree(true).close_all();

  for (var i=0; i < idds.length; i++) {

    var idd = idds[i]; 

    var parent = $('#jstree_b').jstree(true).get_parent(idd);
    var siblings = $('#jstree_b').jstree(true).get_node(parent).children;

    for (var x=0; x < siblings.length ; x++ ) {
      if (idd == siblings[x]) {
        $('#jstree_b').jstree(true).open_node(siblings[x]);
      } else {
        $('#jstree_b').jstree(true).close_node(siblings[x]);
      }
    }

    $('#jstree_b').jstree(true).select_node(idd);
  }
}

function goto(id) {
    $('#myTabs a[href="#detail"]').tab('show') 
    var url = location.href;
    location.href = '#' + id;
    history.replaceState(null,null,url);
}

