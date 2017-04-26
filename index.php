<?php 

include_once ('config.php');


 

//modele : Acces au donnes

  


$manager = new BilletsManager();
 


 

//traitement 
//vue
;?>

	<!DOCTYPE html>
	<html>

	<!-- on récupere le headers  -->
	<?php include_once( 'header.php'); ?>



		<body>


			<?php include_once( 'header_top.php'); ?>

				<?php include_once( 'menu.php'); ?>

					<?php include_once( 'banner.php'); ?>

						<?php include ( 'container_corps.php'); ?>

							<?php include_once( 'footer.php'); ?>

								<?php include ( 'script.php'); ?>


		</body>

	</html>